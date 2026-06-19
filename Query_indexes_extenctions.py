"""
DONE!
"""

def add_geometry_to_stops(conn):
    """Add geom column to stops table and populate with coordinates"""
    with conn.cursor() as cur:
        # Add geom column if it doesn't exist
        cur.execute("ALTER TABLE stops ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);")
        # Populate geom column with coordinates from stop_lat and stop_lon
        cur.execute("""
            UPDATE stops
            SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326)
            WHERE geom IS NULL;
        """)
    conn.commit()

def create_gtfs_indexes(conn):
    queries = [
        "CREATE INDEX IF NOT EXISTS trips_route_id_idx ON trips(route_id);",
        "CREATE INDEX IF NOT EXISTS trips_shape_id_idx ON trips(shape_id);",
        "CREATE INDEX IF NOT EXISTS stop_times_trip_id_idx ON stop_times(trip_id);",
        "CREATE INDEX IF NOT EXISTS stop_times_stop_id_idx ON stop_times(stop_id);",
        "CREATE INDEX IF NOT EXISTS routes_short_name_idx ON routes(route_short_name);",
        "CREATE INDEX IF NOT EXISTS shape_geoms_shape_id_idx ON shape_geoms(shape_id);",
        "CREATE INDEX IF NOT EXISTS trips_service_id_idx ON trips(service_id);",
        "CREATE INDEX IF NOT EXISTS transit_edges_source_idx ON transit_edges(source);",
        "CREATE INDEX IF NOT EXISTS transit_edges_target_idx ON transit_edges(target);",
        "CREATE INDEX IF NOT EXISTS transit_edges_geom_gix ON transit_edges USING GIST (geom);",
        "CREATE INDEX IF NOT EXISTS transit_edges_from_stop_idx ON transit_edges(from_stop_id);",
        "CREATE INDEX IF NOT EXISTS transit_edges_to_stop_idx ON transit_edges(to_stop_id);",
        "CREATE INDEX IF NOT EXISTS stop_vertices_geom_gix ON stop_vertices USING GIST (geom);",
        "CREATE INDEX IF NOT EXISTS stops_geom_gix ON stops USING GIST (geom);"
    ]

    with conn.cursor() as cur:
        for q in queries:
            cur.execute(q)

    conn.commit()

def enable_postgres_extensions(conn):
    queries = [
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "CREATE EXTENSION IF NOT EXISTS pgrouting;"
    ]

    with conn.cursor() as cur:
        for q in queries:
            cur.execute(q)

    conn.commit()