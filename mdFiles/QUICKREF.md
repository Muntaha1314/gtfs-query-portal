# 📋 GTFS Route Planning Backend - Quick Reference

## 🚀 Quick Start (30 seconds)

```bash
# 1. Activate virtual environment
venv\Scripts\activate                    # Windows
source venv/bin/activate                 # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure database credentials
# Edit .env with your database details

# 4. Run verification
python verify_setup.py

# 5. Start API
uvicorn main:app --reload
```

## 📁 Project Structure

```
.
├── main.py                          # FastAPI application
├── db.py                            # Database connection management
├── config.py                        # Configuration from environment
├── verify_setup.py                  # Database setup verification
├── test_api.py                      # API endpoint tests
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── SETUP.md                         # Detailed setup guide
├── API_README.md                    # API documentation
├── QUICKREF.md                      # This file
├── routes/
│   ├── __init__.py
│   ├── stops.py                     # Stop-related endpoints
│   └── routing.py                   # Route planning endpoints
└── sql/
    ├── create_tables.sql            # Create GTFS tables
    ├── add_geometry.sql             # Add spatial columns
    ├── extensions.sql               # Install PostGIS/pgRouting
    ├── indexes.sql                  # Create performance indexes
    ├── cleanup.sql                  # Clean data
    ├── view_outputs.sql             # Create materialized views
    └── setup_pgrouting_network.sql  # Optional: pgRouting setup
```

## 🔧 Environment Variables

Create `.env` file with these variables:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gtfs_db
DB_USER=postgres
DB_PASSWORD=your_password

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## 🌐 API Endpoints

### Health & Info
- `GET /` - API info
- `GET /health` - Database health check

### Stops
- `GET /api/stops?limit=50` - List stops
- `GET /api/stops/{stop_id}` - Stop details
- `GET /api/stops/nearby?lat=X&lon=Y&radius=Z` - Nearby stops

### Routes & Routing
- `GET /api/routes?limit=100` - List routes
- `GET /api/route?start=ID&end=ID` - Find route path
- `GET /api/route-geometry/{route_id}` - Route geometry as GeoJSON

## 📊 Query Examples

### Get Stops
```bash
curl "http://localhost:8000/api/stops?limit=10"
```

### Find Nearby Stops (500m radius)
```bash
curl "http://localhost:8000/api/stops/nearby?lat=40.7128&lon=-74.0060&radius=500"
```

### Find Route Between Stops
```bash
curl "http://localhost:8000/api/route?start=1001&end=1050"
```

### Get All Routes
```bash
curl "http://localhost:8000/api/routes?limit=20"
```

## 🧪 Testing

### Run Verification
```bash
python verify_setup.py
```

### Run API Tests
```bash
python test_api.py
```

### Manual Testing
```bash
# Browser - Swagger UI
http://localhost:8000/docs

# Browser - ReDoc
http://localhost:8000/redoc

# Health check
curl http://localhost:8000/health
```

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Connection refused | Start PostgreSQL service |
| Database not found | Run SQL scripts to create/load data |
| Missing extensions | `CREATE EXTENSION postgis;` in psql |
| Slow nearby queries | Check spatial indexes: `SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE '%gix';` |
| Invalid credentials | Update .env file and restart |

## 📦 Install Dependencies

```bash
# Create virtual environment (first time)
python -m venv venv

# Activate it
venv\Scripts\activate                    # Windows
source venv/bin/activate                 # macOS/Linux

# Install packages
pip install -r requirements.txt
```

## 🚀 Run Modes

### Development (with hot reload)
```bash
uvicorn main:app --reload
```

### Production (Gunicorn)
```bash
gunicorn main:app --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Production (uWSGI)
```bash
pip install uwsgi
uwsgi --ini uwsgi.ini
```

### As Python Package
```bash
pip install build
python -m build
pip install dist/gtfs_route_planning_api-*.whl[prod]
```

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app setup, routers, lifespan |
| `db.py` | Database connection, query helpers |
| `config.py` | Environment configuration |
| `routes/stops.py` | Stops endpoints |
| `routes/routing.py` | Route planning endpoints |
| `verify_setup.py` | Database verification script |
| `test_api.py` | API integration tests |

## 🔌 Database Queries

### PostGIS - Nearby Stops
```sql
SELECT s.stop_id, s.stop_name, ST_Distance(s.geom, point)
FROM stops s
WHERE ST_DWithin(s.geom, point, 500);
```

### GTFS - Connected Stops
```sql
SELECT DISTINCT st2.stop_id
FROM stop_times st1
JOIN stop_times st2 ON st1.trip_id = st2.trip_id
WHERE st1.stop_id = '1001' AND st1.stop_sequence < st2.stop_sequence;
```

### Route Geometry
```sql
SELECT ST_AsGeoJSON(geom) FROM shape_geoms 
WHERE shape_id IN (SELECT DISTINCT shape_id FROM trips WHERE route_id = 'R01');
```

## 💾 Data Model

### Tables
- `stops` - Transit stops (lat/lon, geometry)
- `routes` - Transit routes (name, type, color)
- `trips` - Individual trips (route, service, shape)
- `stop_times` - Stop sequences (arrival/departure times)
- `shapes` - Route geometries (line strings)
- `agency` - Transit agencies
- `calendar` - Service calendars

### Materialized Views (optional)
- `route_shapes` - Routes with geometries
- `route_trip_counts` - Routes with trip counts

### Spatial Indexes
- `stops_geom_gix` - Stop locations (GIST)
- `shape_geoms_geom_gix` - Shape geometries (GIST)

## ✅ Verification Checklist

- [ ] PostgreSQL running
- [ ] GTFS data loaded in database
- [ ] PostGIS/pgRouting extensions created
- [ ] All SQL scripts executed
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` configured with correct credentials
- [ ] `verify_setup.py` passes all checks
- [ ] API starts without errors
- [ ] `/health` endpoint returns healthy
- [ ] `/docs` (Swagger) loads correctly
- [ ] Can retrieve stops and routes
- [ ] Nearby stop search works
- [ ] Route finding works

## 📞 Support Resources

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Setup Guide**: See `SETUP.md`
- **API Reference**: See `API_README.md`
- **Database Scripts**: See `sql/` directory
- **Test Script**: Run `python test_api.py`

## 🎯 Next Steps

1. **Development**: Start with `uvicorn main:app --reload`
2. **Integration**: Connect frontend using API endpoints
3. **Deployment**: Use Docker or Gunicorn for production
4. **Monitoring**: Add logging and metrics
5. **Optimization**: Configure connection pooling, caching
6. **Security**: Add authentication, HTTPS, rate limiting

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Backend**: FastAPI + PostgreSQL + PostGIS + pgRouting
