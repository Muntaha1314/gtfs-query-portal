# GTFS Query Portal

A GTFS-based spatial and spatio-temporal query portal for public transportation data using PostgreSQL, PostGIS, and a modern FastAPI backend.

## Overview

This project focuses on importing GTFS data, storing it in a spatial database, running basic spatial and route-based queries, and providing a REST API for visualization and integration.

The system uses:
- **PostgreSQL + PostGIS** for spatial data storage and queries
- **pgRouting** for route planning algorithms (optional)
- **FastAPI** for a modern REST API backend
- **GTFS Format** for public transportation data

The first phase uses scheduled GTFS data. Real-time data may be added later if a suitable source becomes available.

---

## 🚀 FastAPI Backend

A complete, production-ready backend for spatial route planning with the following features:

### Features
- ✅ REST API with automatic documentation (Swagger UI, ReDoc)
- ✅ Stop queries with geographic filtering
- ✅ Nearby stop search using PostGIS spatial queries
- ✅ Route discovery between stops
- ✅ Route geometry as GeoJSON
- ✅ Database connection pooling and error handling
- ✅ Environment-based configuration
- ✅ CORS support for frontend integration
- ✅ Health checks and monitoring

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure database (.env file)
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 3. Verify setup
python verify_setup.py

# 4. Start API server
uvicorn main:app --reload
```

API will be available at: **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

**Health & Info**
- `GET /` - API information
- `GET /health` - Database health check

**Stops**
- `GET /api/stops` - List all stops (limit: 50-1000)
- `GET /api/stops/{stop_id}` - Get stop details with geometry
- `GET /api/stops/nearby` - Find nearby stops (PostGIS ST_DWithin)

**Routes & Routing**
- `GET /api/routes` - List transit routes
- `GET /api/route` - Find route path between stops
- `GET /api/route-geometry/{route_id}` - Get route as GeoJSON

### Project Structure

```
.
├── main.py                           # FastAPI application
├── db.py                             # Database connection management
├── config.py                         # Configuration
├── verify_setup.py                   # Setup verification
├── test_api.py                       # API tests
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
├── SETUP.md                          # Detailed setup guide
├── API_README.md                     # API documentation
├── QUICKREF.md                       # Quick reference
├── routes/
│   ├── stops.py                      # Stop endpoints
│   └── routing.py                    # Route planning endpoints
└── sql/
    ├── extensions.sql
    ├── create_tables.sql
    ├── add_geometry.sql
    ├── indexes.sql
    ├── cleanup.sql
    ├── view_outputs.sql
    └── setup_pgrouting_network.sql   # Optional: pgRouting network
```

### Documentation Files

- **SETUP.md** - Complete step-by-step setup guide with troubleshooting
- **API_README.md** - Comprehensive API endpoint documentation
- **QUICKREF.md** - Quick reference for common commands and queries

### Testing

```bash
# Run comprehensive API tests
python test_api.py

# Test with curl
curl http://localhost:8000/health
curl http://localhost:8000/api/stops
curl "http://localhost:8000/api/stops/nearby?lat=40.7128&lon=-74.0060&radius=500"
```

---

## Database Setup

The database uses the following structure and components:
