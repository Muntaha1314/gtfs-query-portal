"""
Load GTFS data from CSV files into PostgreSQL database
DONE!
"""

import os
import psycopg2
import pandas as pd
import logging
from dotenv import load_dotenv

from Query_table_creation import (
    create_stop_vertices_table,
    firststep_transit_edges,
    add_time_to_seconds_function,
    create_transit_edges
)

from Query_indexes_extenctions import (
    create_gtfs_indexes,
    enable_postgres_extensions,
    add_geometry_to_stops
)

POSSIBLE_ENCODINGS = [
    "utf-8",
    "cp1254",
]


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_csv_to_utf8():
    """Convert all CSV files to UTF-8 encoding if they aren't already"""
    data_dir = "data"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        file_path = os.path.join(data_dir, csv_file)
        try:
            # Try reading as UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"{csv_file} is already UTF-8, skipping conversion")
        except UnicodeDecodeError:
            # If UTF-8 fails, try CP1254 and convert to UTF-8
            try:
                logger.info(f"Converting {csv_file} from CP1254 to UTF-8...")
                with open(file_path, 'r', encoding='cp1254') as f:
                    content = f.read()
                # Write back as UTF-8
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Successfully converted {csv_file} to UTF-8")
            except Exception as e:
                logger.warning(f"Could not convert {csv_file}: {e}")


def read_csv(file_path):
    last_error = None

    for encoding in POSSIBLE_ENCODINGS:
        try:
            logger.info(f"Trying to read {file_path} with encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            
            # Normalize all object (string) columns to ensure proper UTF-8 handling
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else x)
            
            logger.info(f"Successfully read {file_path} with encoding: {encoding}")
            return df

        except UnicodeDecodeError as e:
            last_error = e
            logger.warning(f"Failed with encoding {encoding}: {e}")

    raise last_error

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "gtfs_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        client_encoding='UTF8'
    )

def load_csv_to_table(csv_file, table_name):
    try:
        logger.info(f"Loading {csv_file} into {table_name}...")
        
        df = read_csv(f"data/{csv_file}")
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Ensure UTF-8 encoding for this session
        cur.execute("SET CLIENT_ENCODING TO 'UTF8';")
        
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
            
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(add_time_to_seconds_function())
        cur.execute(create_stop_vertices_table())
        cur.execute(firststep_transit_edges())
        cur.execute(create_transit_edges())

        conn.commit()

        enable_postgres_extensions(conn)
        add_geometry_to_stops(conn)
        create_gtfs_indexes(conn)

        logger.info(f"Ready to start!")
    
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error loading other functions : {e}")
        raise


def main():
    logger.info("Starting GTFS data import...")
    
    try:
        # First, ensure all CSV files are UTF-8 encoded
        logger.info("Checking and converting CSV files to UTF-8 if needed...")
        convert_csv_to_utf8()
        
        load_csv_to_table("agency.csv", "agency")
        load_csv_to_table("stops.csv", "stops")
        load_csv_to_table("routes.csv", "routes")
        load_csv_to_table("trips.csv", "trips")
        load_csv_to_table("stop_times.csv", "stop_times")
        load_csv_to_table("shapes.csv", "shapes")
        load_csv_to_table("calendar.csv", "calendar")
        
        logger.info("All data loaded successfully!")
        other_functions();
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise



if __name__ == "__main__":
    main()