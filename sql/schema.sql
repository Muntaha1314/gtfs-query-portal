CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;

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



--add geometry

ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);

UPDATE stops
SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);


DROP TABLE IF EXISTS shape_geoms;

CREATE TABLE shape_geoms AS
SELECT
    shape_id,
    ST_MakeLine(
        ST_SetSRID(ST_MakePoint(shape_pt_lon, shape_pt_lat), 4326)
        ORDER BY shape_pt_sequence
    ) AS geom
FROM shapes
GROUP BY shape_id;

------



--tests

SELECT * FROM spatial_ref_sys WHERE srid = 4326;

SELECT PostGIS_full_version();

SELECT COUNT(*) FROM agency;
SELECT COUNT(*) FROM calendar;
SELECT COUNT(*) FROM routes;
SELECT COUNT(*) FROM stops;
SELECT COUNT(*) FROM shapes;
SELECT COUNT(*) FROM trips;
SELECT COUNT(*) FROM stop_times;

SELECT stop_id, stop_name, ST_AsText(geom)
FROM stops
LIMIT 5;

SELECT shape_id, ST_AsText(geom)
FROM shape_geoms
LIMIT 3;


SELECT route_id, route_short_name, route_long_name
FROM routes
LIMIT 10;

SELECT route_id, COUNT(*) AS trip_count
FROM trips
GROUP BY route_id
ORDER BY trip_count DESC
LIMIT 10;

SELECT stop_id, stop_name
FROM stops
WHERE stop_name ILIKE '%METRO%'
LIMIT 20;
----

DROP TABLE IF EXISTS stop_times;
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS shapes;
DROP TABLE IF EXISTS stops;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS calendar;
DROP TABLE IF EXISTS agency;