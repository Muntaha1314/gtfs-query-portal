# 🚀 FastAPI GTFS Backend - Complete Setup Guide

This guide provides step-by-step instructions to get your GTFS spatial route planning API up and running.

## Prerequisites

Before you start, ensure you have:

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Download](https://www.postgresql.org/download/)
- **PostGIS extension** - Installed in PostgreSQL
- **pgRouting extension** (optional) - For advanced routing
- **GTFS data** - CSV files loaded into database using provided SQL scripts

## Step 1: Verify Database Setup

### 1.1 Check PostgreSQL is Running

**Windows:**
```bash
# Check if PostgreSQL service is running
Get-Service | findstr postgres

# Or start it:
net start postgresql-x64-XX
```

**macOS:**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start if needed:
brew services start postgresql
```

**Linux:**
```bash
# Check status
sudo systemctl status postgresql

# Start if needed:
sudo systemctl start postgresql
```

### 1.2 Verify GTFS Data is Loaded

Connect to your database and check:

```bash
# Connect to database
psql -U postgres -d gtfs_db

# Check tables exist
\dt

# Check data exists
SELECT COUNT(*) FROM stops;
SELECT COUNT(*) FROM routes;
SELECT COUNT(*) FROM trips;
SELECT COUNT(*) FROM stop_times;
```

Expected output: All counts should be greater than 0.

### 1.3 Verify Extensions

```sql
-- Check PostGIS
SELECT extname FROM pg_extension WHERE extname = 'postgis';

-- Check pgRouting (if installed)
SELECT extname FROM pg_extension WHERE extname = 'pgrouting';

-- Create them if missing (run as superuser):
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
```

## Step 2: Install Python Dependencies

### 2.1 Create Virtual Environment

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### 2.2 Install Required Packages

```bash
pip install -r requirements.txt
```

This installs:
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **psycopg2-binary** - PostgreSQL adapter
- **pydantic** - Data validation
- **python-dotenv** - Environment variable management

## Step 3: Configure Environment Variables

### 3.1 Create .env File

Copy the example file:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

### 3.2 Edit .env with Your Database Credentials

Open `.env` in a text editor and update:

```env
# Database Configuration
DB_HOST=localhost           # Your PostgreSQL host
DB_PORT=5432               # PostgreSQL port (default: 5432)
DB_NAME=gtfs_db            # Your database name
DB_USER=postgres           # Your PostgreSQL username
DB_PASSWORD=your_password  # Your PostgreSQL password

# FastAPI Configuration
API_PORT=8000              # Port to run API on
API_HOST=0.0.0.0           # Host to bind to (0.0.0.0 = accessible externally)
```

### 3.3 Verify Credentials

```bash
# Test connection (macOS/Linux)
psql -h localhost -U postgres -d gtfs_db -c "SELECT 1"

# Test connection (Windows)
psql -h localhost -U postgres -d gtfs_db -c "SELECT 1"
```

Should return: `?column?` with value `1`

## Step 4: Verify Database Setup

Run the verification script:

```bash
# Activate virtual environment first (if not already active)
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Run verification
python verify_setup.py
```

This checks:
- ✓ Database connection
- ✓ PostGIS and pgRouting extensions
- ✓ All required GTFS tables
- ✓ Geometry columns
- ✓ Data in tables
- ✓ Spatial indexes

Expected output:
```
============================================================
GTFS Route Planning API - Database Verification
============================================================

✓ PASS: Database Connection
✓ PASS: Extensions
✓ PASS: Tables
✓ PASS: Geometry Columns
✓ PASS: Data Statistics
✓ PASS: Indexes
============================================================
✓ All checks passed! Database is ready.

🚀 You can now start the API with:
   uvicorn main:app --reload
```

## Step 5: Start the API Server

### 5.1 Development Mode (with auto-reload)

```bash
# Make sure virtual environment is active
uvicorn main:app --reload
```

Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Will watch for changes in these directories: ['...']
```

### 5.2 Access the API

Open your browser:

- **API Root**: http://localhost:8000
- **Swagger UI (Docs)**: http://localhost:8000/docs
- **ReDoc (Alternative Docs)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 5.3 Test an Endpoint

```bash
# Get stops
curl http://localhost:8000/api/stops

# Get nearby stops
curl "http://localhost:8000/api/stops/nearby?lat=40.7128&lon=-74.0060&radius=1000"

# Get routes
curl http://localhost:8000/api/routes
```

## Step 6: Optional - Setup pgRouting Network (Advanced)

For advanced pgRouting-based route planning:

```bash
# Connect to database
psql -U postgres -d gtfs_db -f sql/setup_pgrouting_network.sql
```

This creates:
- Vertices table (stops as network nodes)
- Edges table (stop connections)
- pgRouting helper functions

Then you can use advanced routing functions:

```sql
-- Find shortest path
SELECT * FROM get_route_details('1001', '1050');

-- Test the function via API
curl "http://localhost:8000/api/route?start=1001&end=1050"
```

## Production Deployment

### Option 1: Gunicorn (Recommended for Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn main:app --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Option 2: uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Create uwsgi.ini configuration
cat > uwsgi.ini << EOF
[uwsgi]
module = wsgi:app
master = true
processes = 4
socket = /var/run/gtfs-api.sock
chmod-socket = 666
http = 127.0.0.1:8000
daemonize = /var/log/gtfs-api.log
EOF

# Run with uWSGI
uwsgi --ini uwsgi.ini

# Access at http://127.0.0.1:8000
```

### Option 3: Python Package Installation

For production deployment, you can package the application:

```bash
# Install build tools
pip install build

# Build distribution package
python -m build

# This creates:
# - dist/gtfs_route_planning_api-1.0.0-py3-none-any.whl
# - dist/gtfs-route-planning-api-1.0.0.tar.gz

# Install on production server
pip install dist/gtfs_route_planning_api-1.0.0-py3-none-any.whl[prod]
```

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for systemd service configuration.

## 🆘 Troubleshooting

### Issue: "could not connect to server: Connection refused"

**Solution:** PostgreSQL is not running
```bash
# Windows: Start PostgreSQL service
net start postgresql-x64-XX

# macOS: Start PostgreSQL
brew services start postgresql

# Linux: Start PostgreSQL
sudo systemctl start postgresql
```

### Issue: "role 'postgres' does not exist"

**Solution:** Create the PostgreSQL user or update DB_USER in .env
```sql
-- In psql
CREATE USER postgres WITH PASSWORD 'password';
ALTER USER postgres SUPERUSER;
```

### Issue: "database 'gtfs_db' does not exist"

**Solution:** Create the database first
```bash
# Using psql
psql -U postgres -c "CREATE DATABASE gtfs_db;"

# Then load GTFS data using the SQL scripts
psql -U postgres -d gtfs_db -f sql/create_tables.sql
psql -U postgres -d gtfs_db -f sql/add_geometry.sql
```

### Issue: "EXTENSION postgis does not exist"

**Solution:** Install PostGIS extension
```sql
-- In psql connected to your database
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
```

### Issue: Verify script says "✗ FAIL" for any check

**Solution:** Review the detailed error messages and check:

1. **Database Connection**: Verify credentials in .env
2. **Extensions**: Install missing extensions
3. **Tables**: Run SQL scripts to create tables
4. **Geometry**: Run `add_geometry.sql` to add spatial columns
5. **Data**: Import GTFS CSV files using provided scripts
6. **Indexes**: Run `indexes.sql` to create performance indexes

### Issue: API returns 500 errors

**Solution:** Check server logs for detailed error messages:

```bash
# Look for error messages in console output
# Common issues:
# - Database credentials incorrect
# - Database not running
# - Tables don't have expected columns
# - Missing geometry columns

# Enable verbose logging (update config.py):
LOG_LEVEL=DEBUG
```

### Issue: Slow queries on nearby stops

**Solution:** Ensure spatial indexes are created:
```sql
-- Check indexes
SELECT indexname FROM pg_indexes WHERE indexname LIKE '%gix';

-- Create if missing (these are run in indexes.sql):
CREATE INDEX stops_geom_gix ON stops USING GIST (geom);
CREATE INDEX shape_geoms_geom_gix ON shape_geoms USING GIST (geom);
```

## Testing Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed with `pip install -r requirements.txt`
- [ ] .env file configured with correct database credentials
- [ ] Database verification passes with `python verify_setup.py`
- [ ] API starts with `uvicorn main:app --reload`
- [ ] Can access http://localhost:8000/docs
- [ ] Health check passes: http://localhost:8000/health
- [ ] `/api/stops` endpoint returns data
- [ ] `/api/stops/nearby?lat=X&lon=Y&radius=Z` works
- [ ] `/api/routes` endpoint returns data
- [ ] `/api/route?start=ID1&end=ID2` finds connections

## Next Steps

1. **Configure CORS** - Update in main.py for your frontend domain
2. **Add Authentication** - Implement JWT or API key auth if needed
3. **Deploy to Production** - Use Gunicorn, uWSGI, or systemd services (see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md))
4. **Monitor Performance** - Add logging and metrics
5. **Scale Database** - Add connection pooling for high load

## Useful Commands

```bash
# Activate virtual environment
venv\Scripts\activate                # Windows
source venv/bin/activate             # macOS/Linux

# Install requirements
pip install -r requirements.txt

# Run verification
python verify_setup.py

# Start development server
uvicorn main:app --reload

# Start production server
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Check database tables
psql -U postgres -d gtfs_db -c "\dt"

# Check data counts
psql -U postgres -d gtfs_db -c "SELECT COUNT(*) FROM stops;"

# View API docs
# Open browser to http://localhost:8000/docs
```

## Support

For additional help:
- Check API documentation at http://localhost:8000/docs
- Review error messages in console output
- Check `.env` configuration
- Ensure database is running and accessible
- Verify all SQL scripts were executed in correct order
