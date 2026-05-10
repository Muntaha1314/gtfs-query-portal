--schema


DROP MATERIALIZED VIEW IF EXISTS route_shapes;

CREATE MATERIALIZED VIEW route_shapes AS
SELECT DISTINCT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    t.shape_id,
    sg.geom
FROM routes r
JOIN trips t ON r.route_id = t.route_id
JOIN shape_geoms sg ON t.shape_id = sg.shape_id;

CREATE INDEX IF NOT EXISTS route_shapes_geom_gix ON route_shapes USING GIST (geom);



DROP MATERIALIZED VIEW IF EXISTS route_trip_counts;

CREATE MATERIALIZED VIEW route_trip_counts AS
SELECT
    rs.route_id,
    rs.route_short_name,
    rs.route_long_name,
    COUNT(DISTINCT t.trip_id) AS trip_count,
    rs.geom
FROM route_shapes rs
JOIN trips t
  ON rs.route_id = t.route_id
 AND rs.shape_id = t.shape_id
GROUP BY rs.route_id, rs.route_short_name, rs.route_long_name, rs.shape_id, rs.geom;

-----


--Full network output
--Input needed: none
--Output returned: route_id, route_short_name, route_long_name, geojson
--Used for: displaying the full transit network on the map

SELECT
    route_id,
    route_short_name,
    route_long_name,
    ST_AsGeoJSON(geom) AS geojson
FROM route_shapes;


--One selected route + stops
--Input needed: route_id
--Output returned:stop_id, stop_name, stop_sequence, stop_geojson
--Used for: displaying one selected route’s stops in order

WITH one_trip AS (
    SELECT trip_id, shape_id
    FROM trips
    WHERE route_id = '28195'
    LIMIT 1
)
SELECT
    s.stop_id,
    s.stop_name,
    st.stop_sequence,
    ST_AsGeoJSON(s.geom) AS stop_geojson
FROM one_trip ot
JOIN stop_times st ON ot.trip_id = st.trip_id
JOIN stops s ON st.stop_id = s.stop_id
ORDER BY st.stop_sequence;


--Top routes by trip count
--Input needed: none
--Output returned: route_id, route_short_name, route_long_name, trip_count
--Used for: showing the busiest or most scheduled routes

SELECT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    COUNT(t.trip_id) AS trip_count
FROM routes r
JOIN trips t ON r.route_id = t.route_id
GROUP BY r.route_id, r.route_short_name, r.route_long_name
ORDER BY trip_count DESC
LIMIT 20;


--Busiest stops in morning hours
--Input needed: start time, end time
--Output returned: stop_id, stop_name, morning_arrivals, geojson
--Used for: showing the busiest stops during morning hours on the map or in ranking form

SELECT
    s.stop_id,
    s.stop_name,
    COUNT(*) AS morning_arrivals,
    ST_AsGeoJSON(s.geom) AS geojson
FROM stop_times st
JOIN stops s ON st.stop_id = s.stop_id
WHERE st.arrival_time >= '07:00:00'
  AND st.arrival_time < '09:00:00'
GROUP BY s.stop_id, s.stop_name, s.geom
ORDER BY morning_arrivals DESC
LIMIT 20;


