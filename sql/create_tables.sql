--create tables

CREATE TABLE agency (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT,
    agency_url TEXT,
    agency_timezone TEXT,
    agency_lang TEXT,
    agency_phone TEXT,
    agency_fare_url TEXT,
    agency_email TEXT
);

CREATE TABLE calendar (
    service_id TEXT PRIMARY KEY,
    monday INTEGER,
    tuesday INTEGER,
    wednesday INTEGER,
    thursday INTEGER,
    friday INTEGER,
    saturday INTEGER,
    sunday INTEGER,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT
);

CREATE TABLE stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT,
    stop_desc TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    zone_id TEXT,
    stop_url TEXT,
    location_type INTEGER,
    parent_station TEXT,
    stop_timezone TEXT,
    wheelchair_boarding INTEGER
);

CREATE TABLE shapes (
    shape_id TEXT,
    shape_pt_lat DOUBLE PRECISION,
    shape_pt_lon DOUBLE PRECISION,
    shape_pt_sequence INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

CREATE TABLE trips (
    route_id TEXT,
    service_id TEXT,
    trip_id TEXT PRIMARY KEY,
    trip_headsign TEXT,
    trip_short_name TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    wheelchair_accessible INTEGER,
    bikes_allowed INTEGER
);

CREATE TABLE stop_times (
    trip_id TEXT,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT,
    stop_sequence INTEGER,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    timepoint INTEGER,
    PRIMARY KEY (trip_id, stop_sequence)
);


-----
DROP TABLE IF EXISTS stop_vertices;

CREATE TABLE stop_vertices AS
SELECT
    row_number() OVER (ORDER BY stop_id) AS vertex_id,
    stop_id,
    stop_name,
    geom
FROM stops;

ALTER TABLE stop_vertices
ADD PRIMARY KEY (vertex_id);

CREATE UNIQUE INDEX stop_vertices_stop_id_idx ON stop_vertices(stop_id);
CREATE INDEX stop_vertices_geom_gix ON stop_vertices USING GIST (geom);



DROP TABLE IF EXISTS transit_edges_raw;

CREATE TABLE transit_edges_raw AS
SELECT
    st1.trip_id,
    st1.stop_id AS from_stop_id,
    st2.stop_id AS to_stop_id,
    st1.stop_sequence AS from_seq,
    st2.stop_sequence AS to_seq,
    GREATEST(
        gtfs_time_to_seconds(st2.arrival_time) -
        gtfs_time_to_seconds(st1.departure_time),
        1
    ) AS travel_seconds
FROM stop_times st1
JOIN stop_times st2
  ON st1.trip_id = st2.trip_id
 AND st2.stop_sequence = st1.stop_sequence + 1
WHERE st1.stop_id <> st2.stop_id;



DROP TABLE IF EXISTS transit_edges;

CREATE TABLE transit_edges AS
SELECT
    row_number() OVER () AS id,
    v1.vertex_id AS source,
    v2.vertex_id AS target,
    r.from_stop_id,
    r.to_stop_id,
    AVG(r.travel_seconds)::double precision AS cost,
    ST_MakeLine(s1.geom, s2.geom)::geometry(LineString, 4326) AS geom,
    ST_X(s1.geom) AS x1,
    ST_Y(s1.geom) AS y1,
    ST_X(s2.geom) AS x2,
    ST_Y(s2.geom) AS y2
FROM transit_edges_raw r
JOIN stop_vertices v1 ON r.from_stop_id = v1.stop_id
JOIN stop_vertices v2 ON r.to_stop_id = v2.stop_id
JOIN stops s1 ON r.from_stop_id = s1.stop_id
JOIN stops s2 ON r.to_stop_id = s2.stop_id
GROUP BY
    v1.vertex_id, v2.vertex_id,
    r.from_stop_id, r.to_stop_id,
    s1.geom, s2.geom;

ALTER TABLE transit_edges
ADD PRIMARY KEY (id);