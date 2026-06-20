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

def check_if_tables_populated():
    """Check if main tables already have data to avoid re-loading"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stops;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        logger.info(f"Tables not yet initialized: {e}")
        return False

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


def check_if_demo_data_loaded():
    """Check if demo vehicle data already exists"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM realtime_vehicles;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        logger.info(f"Demo data check: {e}")
        return False

def load_demo_rt_data():
    """Load synthetic demo vehicle trajectory data for testing Mobility tab"""
    logger.info("Loading demo real-time vehicle data...")
    
    try:
        # Check if demo data already loaded
        if check_if_demo_data_loaded():
            logger.info("Demo vehicle data already loaded, skipping...")
            return
        
        conn = get_connection()
        cur = conn.cursor()
        
        demo_data = []
        
        # Vehicle V101 on M1 route - North-South movement (larger visible arc)
        # Starting from south: 41.00, ending north: 41.10
        base_lat, base_lon = 41.00, 29.00
        for i in range(25):
            timestamp = f"2026-05-25 08:00:{i*2:02d}+03"
            lat = base_lat + (i * 0.004)  # Moves 0.1 degrees over 25 steps
            lon = base_lon
            demo_data.append((f"V101", f"M1", lat, lon, 0.0, 25.0, timestamp))
        
        # Vehicle V102 on M2 route - East-West movement
        # Starting from west: 28.95, ending east: 29.05
        base_lat, base_lon = 41.05, 28.95
        for i in range(25):
            timestamp = f"2026-05-25 08:00:{i*2:02d}+03"
            lat = base_lat
            lon = base_lon + (i * 0.004)  # Moves 0.1 degrees
            demo_data.append((f"V102", f"M2", lat, lon, 90.0, 22.0, timestamp))
        
        # Vehicle V103 on M3 route - Northeast diagonal
        # Moves both north and east
        base_lat, base_lon = 41.02, 28.97
        for i in range(25):
            timestamp = f"2026-05-25 08:00:{i*2:02d}+03"
            lat = base_lat + (i * 0.0025)
            lon = base_lon + (i * 0.0035)
            demo_data.append((f"V103", f"M3", lat, lon, 45.0, 20.0, timestamp))
        
        # Vehicle V104 on M4 route - Complex route (zigzag)
        # Creates visible distinct path
        base_lat, base_lon = 41.08, 29.02
        for i in range(25):
            timestamp = f"2026-05-25 08:00:{i*2:02d}+03"
            # Zigzag pattern: goes down and right alternately
            if i % 5 == 0:
                lat = base_lat - (i * 0.002)
                lon = base_lon
            elif i % 5 < 3:
                lat = base_lat - (i * 0.002)
                lon = base_lon + (i * 0.002)
            else:
                lat = base_lat - (i * 0.002)
                lon = base_lon
            demo_data.append((f"V104", f"M4", lat, lon, 225.0, 18.0, timestamp))
        
        # Insert demo data
        insert_query = """
            INSERT INTO realtime_vehicles 
            (vehicle_id, route_id, latitude, longitude, heading, speed, "timestamp")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.executemany(insert_query, demo_data)
        conn.commit()
        
        logger.info(f"Loaded {len(demo_data)} demo vehicle positions (4 vehicles × 25 positions)")
        logger.info("Trajectories will be auto-generated from vehicle positions via trigger")
        logger.info("Demo vehicles: V101 (M1 North-South), V102 (M2 East-West), V103 (M3 Diagonal), V104 (M4 Complex)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading demo RT data: {e}")
        raise

def main():
    logger.info("Starting GTFS data import...")
    
    try:
        # Check if data is already loaded
        if check_if_tables_populated():
            logger.info("GTFS data already loaded, skipping import...")
            # But still load demo data if needed
            load_demo_rt_data()
            return
        
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
        other_functions()
        
        # Load demo vehicle trajectory data for testing
        load_demo_rt_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise



if __name__ == "__main__":
    main()