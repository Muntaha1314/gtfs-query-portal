-- Optional: Create pgRouting network edges from GTFS data
-- This creates a basic edges table for pgRouting dijkstra queries
-- Run this if you want to use pgr_dijkstra for route planning

-- Create edges table with transit connections
CREATE TABLE IF NOT EXISTS edges (
    id BIGSERIAL PRIMARY KEY,
    source INTEGER NOT NULL,
    target INTEGER NOT NULL,
    cost FLOAT NOT NULL,
    reverse_cost FLOAT NOT NULL DEFAULT -1,
    geom GEOMETRY(LineString, 4326)
);

-- Create vertices table (one vertex per stop)
CREATE TABLE IF NOT EXISTS vertices (
    id BIGSERIAL PRIMARY KEY,
    stop_id TEXT UNIQUE NOT NULL,
    stop_name TEXT,
    geom GEOMETRY(Point, 4326)
);

-- Insert stops as vertices
INSERT INTO vertices (stop_id, stop_name, geom)
SELECT stop_id, stop_name, geom FROM stops
ON CONFLICT (stop_id) DO NOTHING;

-- Create edges from stop_times sequences (direct connections)
INSERT INTO edges (source, target, cost, reverse_cost, geom)
SELECT 
    v1.id as source,
    v2.id as target,
    ST_Distance(s1.geom, s2.geom, true) / 1000.0 as cost,  -- Cost in km for realistic weights
    ST_Distance(s2.geom, s1.geom, true) / 1000.0 as reverse_cost,
    ST_MakeLine(s1.geom, s2.geom) as geom
FROM stop_times st1
JOIN stop_times st2 ON st1.trip_id = st2.trip_id 
    AND st2.stop_sequence = st1.stop_sequence + 1
JOIN stops s1 ON st1.stop_id = s1.stop_id
JOIN stops s2 ON st2.stop_id = s2.stop_id
JOIN vertices v1 ON s1.stop_id = v1.stop_id
JOIN vertices v2 ON s2.stop_id = v2.stop_id
ON CONFLICT DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS edges_source_target_idx ON edges (source, target);
CREATE INDEX IF NOT EXISTS edges_geom_gix ON edges USING GIST (geom);
CREATE INDEX IF NOT EXISTS vertices_geom_gix ON vertices USING GIST (geom);

-- Create topology for pgRouting (if needed for other algorithms)
-- This may take some time depending on dataset size
SELECT pgr_createTopology('edges', 0.001, 'geom', 'id', 'source', 'target');

-- Test function to find shortest path between stops
-- Usage: SELECT * FROM find_shortest_path('stop_id_1', 'stop_id_2');
CREATE OR REPLACE FUNCTION find_shortest_path(start_stop_id TEXT, end_stop_id TEXT)
RETURNS TABLE(seq INT, path_seq INT, node BIGINT, edge BIGINT, cost FLOAT, agg_cost FLOAT) AS $$
DECLARE
    start_id BIGINT;
    end_id BIGINT;
BEGIN
    -- Get vertex IDs from stop IDs
    SELECT id INTO start_id FROM vertices WHERE stop_id = start_stop_id LIMIT 1;
    SELECT id INTO end_id FROM vertices WHERE stop_id = end_stop_id LIMIT 1;
    
    IF start_id IS NULL OR end_id IS NULL THEN
        RAISE EXCEPTION 'Start or end stop not found';
    END IF;
    
    -- Run dijkstra algorithm
    RETURN QUERY
    SELECT * FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM edges',
        start_id,
        end_id,
        false
    );
END;
$$ LANGUAGE plpgsql;

-- Create view to get path details with stop information
CREATE OR REPLACE VIEW route_path AS
SELECT 
    p.seq,
    p.node,
    v.stop_id,
    v.stop_name,
    s.stop_lat,
    s.stop_lon,
    p.cost,
    p.agg_cost,
    e.geom
FROM pgr_dijkstra(
    'SELECT id, source, target, cost FROM edges',
    1, 5, false
) AS p
LEFT JOIN vertices v ON p.node = v.id
LEFT JOIN stops s ON v.stop_id = s.stop_id
LEFT JOIN edges e ON p.edge = e.id;

-- Additional helper function for detailed route information
CREATE OR REPLACE FUNCTION get_route_details(start_stop_id TEXT, end_stop_id TEXT)
RETURNS TABLE(
    sequence INT,
    stop_id TEXT,
    stop_name TEXT,
    stop_lat FLOAT,
    stop_lon FLOAT,
    distance_km FLOAT,
    cumulative_distance_km FLOAT
) AS $$
DECLARE
    start_id BIGINT;
    end_id BIGINT;
BEGIN
    SELECT id INTO start_id FROM vertices WHERE stop_id = start_stop_id LIMIT 1;
    SELECT id INTO end_id FROM vertices WHERE stop_id = end_stop_id LIMIT 1;
    
    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY p.seq) as sequence,
        v.stop_id,
        v.stop_name,
        s.stop_lat::FLOAT,
        s.stop_lon::FLOAT,
        p.cost::FLOAT as distance_km,
        p.agg_cost::FLOAT as cumulative_distance_km
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM edges',
        start_id,
        end_id,
        false
    ) AS p
    JOIN vertices v ON p.node = v.id
    JOIN stops s ON v.stop_id = s.stop_id
    ORDER BY p.seq;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM find_shortest_path('1001', '1050');
-- SELECT * FROM get_route_details('1001', '1050');

-- Note: This creates a simple network where all stop-to-stop connections
-- have equal weight (1 km cost). You may want to adjust costs based on:
-- - Actual travel time
-- - Route frequency
-- - Transfer penalties
-- - Stop distance from route shape
