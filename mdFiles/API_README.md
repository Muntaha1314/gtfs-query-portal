# GTFS Spatial Route Planning API

A clean, production-ready FastAPI backend for spatial route planning using GTFS data, PostgreSQL, PostGIS, and pgRouting.

## 📋 Features

- ✅ **REST API** - FastAPI with automatic Swagger UI documentation
- ✅ **Spatial Queries** - PostGIS integration for geographic queries
- ✅ **Route Planning** - Find paths between stops using GTFS stop_times
- ✅ **Nearby Search** - Find stops within a radius using ST_DWithin
- ✅ **Database Connection** - Secure connection using environment variables
- ✅ **Error Handling** - Comprehensive error handling with proper HTTP status codes
- ✅ **CORS Support** - Ready for frontend integration
- ✅ **Health Checks** - Database connectivity monitoring

## 🏗️ Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── db.py                   # Database connection management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── routes/
│   ├── __init__.py
│   ├── stops.py           # Stops endpoints
│   └── routing.py         # Route planning endpoints
└── sql/                   # (Pre-existing) Database scripts
    ├── extensions.sql     # PostGIS, pgRouting extensions
    ├── create_tables.sql  # GTFS table creation
    ├── add_geometry.sql   # Spatial geometry setup
    ├── indexes.sql        # Performance indexes
    ├── cleanup.sql        # Data cleaning
    └── view_outputs.sql   # Materialized views
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ with PostGIS and pgRouting extensions
- GTFS data already loaded into database
- All SQL scripts executed

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update with your database credentials:

```bash
# On Windows:
copy .env.example .env

# On macOS/Linux:
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gtfs_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# With custom host/port
uvicorn main:app --host 127.0.0.1 --port 8080
```

The API will be available at: **http://localhost:8000**

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Health Checks

#### `GET /`
Root endpoint with API information.

```bash
curl http://localhost:8000/
```

#### `GET /health`
Health check with database connectivity status.

```bash
curl http://localhost:8000/health
```

---

### Stops

#### `GET /api/stops`
Get list of stops (limited to 50 by default).

**Parameters:**
- `limit` (int, optional): Number of stops to return (default: 50, max: 1000)

**Example:**
```bash
curl "http://localhost:8000/api/stops?limit=100"
```

**Response:**
```json
{
  "count": 50,
  "limit": 50,
  "stops": [
    {
      "stop_id": "1001",
      "stop_name": "Main Station",
      "stop_lat": 40.7128,
      "stop_lon": -74.0060,
      "stop_code": "MS",
      "stop_desc": "Main Transit Hub"
    }
  ]
}
```

---

#### `GET /api/stops/{stop_id}`
Get detailed information about a specific stop.

**Example:**
```bash
curl http://localhost:8000/api/stops/1001
```

**Response:**
```json
{
  "stop_id": "1001",
  "stop_code": "MS",
  "stop_name": "Main Station",
  "stop_desc": "Main Transit Hub",
  "stop_lat": 40.7128,
  "stop_lon": -74.0060,
  "zone_id": "1",
  "stop_url": "https://transit.example.com/stops/1001",
  "location_type": 1,
  "parent_station": null,
  "stop_timezone": "America/New_York",
  "wheelchair_boarding": 1,
  "geojson": "{\"type\": \"Point\", \"coordinates\": [-74.0060, 40.7128]}"
}
```

---

#### `GET /api/stops/nearby`
Find stops near a location using PostGIS spatial queries.

**Parameters:**
- `lat` (float, required): Latitude (-90 to 90)
- `lon` (float, required): Longitude (-180 to 180)
- `radius` (float, optional): Search radius in meters (default: 500, range: 10-50000)

**Example:**
```bash
curl "http://localhost:8000/api/stops/nearby?lat=40.7128&lon=-74.0060&radius=1000"
```

**Response:**
```json
{
  "lat": 40.7128,
  "lon": -74.0060,
  "radius_meters": 1000,
  "count": 15,
  "stops": [
    {
      "stop_id": "1001",
      "stop_name": "Main Station",
      "stop_lat": 40.7128,
      "stop_lon": -74.0060,
      "distance_meters": 0.0
    },
    {
      "stop_id": "1002",
      "stop_name": "Central Hub",
      "stop_lat": 40.7150,
      "stop_lon": -74.0075,
      "distance_meters": 287.45
    }
  ]
}
```

---

### Routes

#### `GET /api/routes`
Get list of all transit routes with trip counts.

**Parameters:**
- `limit` (int, optional): Number of routes to return (default: 100, max: 1000)

**Example:**
```bash
curl "http://localhost:8000/api/routes?limit=50"
```

**Response:**
```json
{
  "count": 42,
  "routes": [
    {
      "route_id": "R01",
      "route_short_name": "1",
      "route_long_name": "Downtown Express",
      "route_type": 3,
      "agency_id": "AGENCY1",
      "route_color": "FF0000"
    }
  ]
}
```

---

#### `GET /api/route`
Find a route path between two stops.

**Parameters:**
- `start` (string, required): Start stop ID
- `end` (string, required): End stop ID
- `exclude_walk` (boolean, optional): Exclude walking transfers (default: true)

**Example:**
```bash
curl "http://localhost:8000/api/route?start=1001&end=1050"
```

**Response:**
```json
{
  "start_stop_id": "1001",
  "end_stop_id": "1050",
  "path_found": true,
  "total_stops": 12,
  "distance_meters": 3450.75,
  "path": [
    {
      "stop_id": "1001",
      "stop_name": "Main Station",
      "stop_lat": 40.7128,
      "stop_lon": -74.0060,
      "sequence": 1
    },
    {
      "stop_id": "1010",
      "stop_name": "Park Avenue",
      "stop_lat": 40.7250,
      "stop_lon": -74.0100,
      "sequence": 2
    }
  ]
}
```

---

#### `GET /api/route-geometry/{route_id}`
Get complete geometry of a route as GeoJSON (shapes + stops).

**Example:**
```bash
curl http://localhost:8000/api/route-geometry/R01
```

**Response:**
```json
{
  "type": "FeatureCollection",
  "properties": {
    "route_id": "R01",
    "route_short_name": "1",
    "route_long_name": "Downtown Express",
    "route_color": "FF0000"
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-74.0060, 40.7128], [-74.0075, 40.7150]]
      },
      "properties": {
        "type": "route_shape",
        "shape_id": "SHAPE001"
      }
    }
  ]
}
```

---

## 🧪 Testing Endpoints

### Using curl

```bash
# Test database connectivity
curl http://localhost:8000/health

# Get all stops
curl http://localhost:8000/api/stops

# Get nearby stops
curl "http://localhost:8000/api/stops/nearby?lat=40.7128&lon=-74.0060&radius=500"

# Get a specific stop
curl http://localhost:8000/api/stops/1001

# Get all routes
curl http://localhost:8000/api/routes

# Find a route between stops
curl "http://localhost:8000/api/route?start=1001&end=1050"

# Get route geometry
curl http://localhost:8000/api/route-geometry/R01
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get stops
response = requests.get(f"{BASE_URL}/api/stops", params={"limit": 10})
print(response.json())

# Get nearby stops
response = requests.get(
    f"{BASE_URL}/api/stops/nearby",
    params={"lat": 40.7128, "lon": -74.0060, "radius": 1000}
)
print(response.json())

# Find a route
response = requests.get(
    f"{BASE_URL}/api/route",
    params={"start": "1001", "end": "1050"}
)
print(response.json())
```

---

## 🔧 Configuration

### Database Credentials

Set these environment variables in `.env`:

```
DB_HOST=localhost        # PostgreSQL host
DB_PORT=5432            # PostgreSQL port
DB_NAME=gtfs_db         # Database name
DB_USER=postgres        # Database user
DB_PASSWORD=postgres    # Database password
```

### CORS Configuration

The API has CORS enabled for all origins (`allow_origins=["*"]`). For production, update in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific frontend URL
    allow_credentials=True,
    allow_methods=["GET"],  # Restrict to needed methods
    allow_headers=["*"],
)
```

---

## 🐛 Error Handling

The API returns standard HTTP error codes:

- **200** - Success
- **404** - Resource not found
- **422** - Invalid input parameters
- **500** - Server error

**Error Response Example:**
```json
{
  "detail": "Stop 99999 not found"
}
```

---

## 📊 Database Queries Reference

### Finding nearby stops (PostGIS)
```sql
SELECT s.stop_id, s.stop_name, 
       ST_Distance(s.geom, ST_MakePoint(-74.0060, 40.7128)) 
FROM stops s
WHERE ST_DWithin(s.geom, ST_MakePoint(-74.0060, 40.7128), 500);
```

### Finding connected stops (GTFS stop_times)
```sql
SELECT DISTINCT st2.stop_id
FROM stop_times st1
JOIN stop_times st2 ON st1.trip_id = st2.trip_id
WHERE st1.stop_id = '1001'
  AND st1.stop_sequence < st2.stop_sequence;
```

### Getting route geometry (PostGIS)
```sql
SELECT ST_AsGeoJSON(geom) FROM shape_geoms 
WHERE shape_id IN (SELECT DISTINCT shape_id FROM trips WHERE route_id = 'R01');
```

---

## 🚀 Deployment

### Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using uWSGI

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
```

### Python Package Installation

```bash
# Build distribution package
pip install build
python -m build

# Install the built package
pip install dist/gtfs_route_planning_api-1.0.0-py3-none-any.whl[prod]
```

For detailed production deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

---

## 📝 Notes

- All spatial queries use SRID 4326 (WGS84 coordinates - latitude/longitude)
- Distance calculations use spheroid for accurate Earth measurements
- The API handles invalid inputs gracefully with descriptive error messages
- Connection pooling can be added for production using sqlalchemy or psycopg2 pool
- All queries use parameterized statements to prevent SQL injection

---

## 📞 Support

For issues or questions about endpoints, check:
- Swagger UI: http://localhost:8000/docs
- Database logs for connection issues
- API logs in console output

---

## 📄 License

Internal project - GTFS Route Planning System
