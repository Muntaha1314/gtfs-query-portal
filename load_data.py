
import os
import psycopg2
import pandas as pd
import logging
from dotenv import load_dotenv

from database_Creation import connect_Database

from RQuery_table_creation import (
    create_stop_vertices_table,
    firststep_transit_edges,
    add_time_to_seconds_function,
    create_transit_edges,
    add_route_types_table,
    create_shape_geoms_table,
    create_location_types_table
)

from RQuery_indexes import (
    create_gtfs_indexes,
    enable_postgres_extensions
)

from RQuery_MobilityDB_Tranformation import (
    create_trips_mdb,
    create_trips_input_table,
    trips_point_table,
    create_trip_segments_table,
    create_trips_stops_table,
    servis_id_table
)

POSSIBLE_ENCODINGS = [
    "utf-8",
    "cp1254",
]


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_csv(file_path):
    last_error = None

    for encoding in POSSIBLE_ENCODINGS:
        try:
            logger.info(f"Trying to read {file_path} with encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"Successfully read {file_path} with encoding: {encoding}")
            return df

        except UnicodeDecodeError as e:
            last_error = e
            logger.warning(f"Failed with encoding {encoding}: {e}")

    raise last_error

def load_csv_to_table(csv_file, table_name):
    try:
        logger.info(f"Loading {csv_file} into {table_name}...")
        
        df = read_csv(f"data/{csv_file}")        
        conn = connect_Database()
        cur = conn.cursor()
        
        cur.execute(f"TRUNCATE TABLE {table_name};")
        
        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cur.execute(insert_query, tuple(row))
        
        conn.commit()
        logger.info(f"Loaded {len(df)} rows into {table_name}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading {csv_file}: {e}")
        raise

def other_functions():
    try:
        logger.info(f"Creating more tables and indexes...")
            
        conn = connect_Database()
        cur = conn.cursor()

        cur.execute(add_time_to_seconds_function())
        cur.execute(create_stop_vertices_table())
        cur.execute(firststep_transit_edges())
        cur.execute(create_transit_edges())
        cur.execute(add_route_types_table())
        cur.execute(create_shape_geoms_table())
        cur.execute(create_location_types_table())

        conn.commit()

        enable_postgres_extensions(conn)
        create_gtfs_indexes(conn)

        logger.info(f"Ready to start!")
    
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error loading other functions : {e}")
        raise


def moblility_tables():
    try:
        logger.info(f"Creating MobilityDB tables...")
            
        conn = connect_Database()
        cur = conn.cursor()

        cur.execute(servis_id_table())
        cur.execute(create_trips_stops_table())
        cur.execute(create_trip_segments_table())
        cur.execute(trips_point_table())
        cur.execute(create_trips_input_table())
        cur.execute(create_trips_mdb())

        conn.commit()

        logger.info(f"MobilityDB tables created successfully!")
    
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error creating MobilityDB tables: {e}")
        raise


def main():
    logger.info("Starting GTFS data import...")
    
    try:
        load_csv_to_table("agency.csv", "agency")
        load_csv_to_table("stops.csv", "stops")
        load_csv_to_table("routes.csv", "routes")
        load_csv_to_table("trips.csv", "trips")
        load_csv_to_table("stop_times.csv", "stop_times")
        load_csv_to_table("shapes.csv", "shapes")
        load_csv_to_table("calendar.csv", "calendar")
        
        logger.info("All data loaded successfully!")
        other_functions()
        moblility_tables()
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise



if __name__ == "__main__":
    main()