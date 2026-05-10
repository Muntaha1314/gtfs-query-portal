"""
Setup and verification script for GTFS Route Planning API
Checks database connectivity and verifies required tables and extensions
"""

import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_db_cursor, get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def check_database_connection():
    """Check if database is accessible"""
    logger.info("🔍 Checking database connection...")
    try:
        conn = get_connection()
        conn.close()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def check_extensions():
    """Check if PostGIS and pgRouting extensions are installed"""
    logger.info("🔍 Checking PostGIS and pgRouting extensions...")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('postgis', 'pgrouting')
            """)
            extensions = [row['extname'] for row in cursor.fetchall()]
            
            required = {'postgis', 'pgrouting'}
            missing = required - set(extensions)
            
            if not missing:
                logger.info(f"✓ All extensions installed: {extensions}")
                return True
            else:
                logger.warning(f"⚠ Missing extensions: {missing}")
                return False
    except Exception as e:
        logger.error(f"✗ Error checking extensions: {e}")
        return False


def check_tables():
    """Check if all required GTFS tables exist"""
    logger.info("🔍 Checking GTFS tables...")
    required_tables = [
        'agency', 'calendar', 'routes', 'stops', 'shapes', 'trips', 'stop_times'
    ]
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            existing_tables = {row['table_name'] for row in cursor.fetchall()}
            
            missing = set(required_tables) - existing_tables
            
            if not missing:
                logger.info(f"✓ All required tables present: {required_tables}")
                return True
            else:
                logger.error(f"✗ Missing tables: {missing}")
                return False
    except Exception as e:
        logger.error(f"✗ Error checking tables: {e}")
        return False


def check_geometry_columns():
    """Check if geometry columns are set up"""
    logger.info("🔍 Checking geometry columns...")
    try:
        with get_db_cursor() as cursor:
            # Check stops.geom
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'stops' AND column_name = 'geom'
            """)
            has_stops_geom = cursor.fetchone() is not None
            
            # Check shape_geoms table
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'shape_geoms'
            """)
            has_shape_geoms = cursor.fetchone() is not None
            
            if has_stops_geom and has_shape_geoms:
                logger.info("✓ Geometry columns set up correctly")
                return True
            else:
                logger.warning("⚠ Missing geometry columns or shape_geoms table")
                return False
    except Exception as e:
        logger.error(f"✗ Error checking geometry columns: {e}")
        return False


def check_data_stats():
    """Check data statistics in tables"""
    logger.info("🔍 Checking data statistics...")
    try:
        with get_db_cursor() as cursor:
            tables_to_check = {
                'stops': 'stop_id',
                'routes': 'route_id',
                'trips': 'trip_id',
                'stop_times': 'trip_id',
                'shapes': 'shape_id',
                'agency': 'agency_id',
                'calendar': 'service_id'
            }
            
            stats = {}
            all_good = True
            
            for table, _ in tables_to_check.items():
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                stats[table] = count
                
                if count == 0:
                    logger.warning(f"⚠ Table '{table}' is empty")
                    all_good = False
                else:
                    logger.info(f"  • {table}: {count:,} rows")
            
            if all_good:
                logger.info("✓ All tables have data")
            else:
                logger.warning("⚠ Some tables are empty")
            
            return all_good
    except Exception as e:
        logger.error(f"✗ Error checking data: {e}")
        return False


def check_indexes():
    """Check if spatial indexes are created"""
    logger.info("🔍 Checking spatial indexes...")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname LIKE '%gix' OR indexname LIKE '%geom%'
            """)
            indexes = [row['indexname'] for row in cursor.fetchall()]
            
            if indexes:
                logger.info(f"✓ Found {len(indexes)} spatial indexes")
                for idx in indexes[:5]:
                    logger.info(f"  • {idx}")
                return True
            else:
                logger.warning("⚠ No spatial indexes found")
                return False
    except Exception as e:
        logger.error(f"✗ Error checking indexes: {e}")
        return False


def run_all_checks():
    """Run all verification checks"""
    logger.info("\n" + "="*60)
    logger.info("GTFS Route Planning API - Database Verification")
    logger.info("="*60 + "\n")
    
    checks = [
        ("Database Connection", check_database_connection),
        ("Extensions", check_extensions),
        ("Tables", check_tables),
        ("Geometry Columns", check_geometry_columns),
        ("Data Statistics", check_data_stats),
        ("Indexes", check_indexes),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"✗ {name} check failed with exception: {e}")
            results[name] = False
        logger.info("")
    
    logger.info("="*60)
    logger.info("Summary:")
    logger.info("="*60)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    all_passed = all(results.values())
    logger.info("="*60 + "\n")
    
    if all_passed:
        logger.info("✓ All checks passed! Database is ready.")
        logger.info("\n🚀 You can now start the API with:")
        logger.info("   uvicorn main:app --reload")
        return 0
    else:
        logger.error("✗ Some checks failed. Please review the database setup.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_checks())
