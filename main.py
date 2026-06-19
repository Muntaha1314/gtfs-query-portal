""""
This is the main file for the project.
FastAPI Backend is implemented here.
Connects to PostgreSQL with PostGIS and pgRouting.

done!
"""

from dotenv import load_dotenv  
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

import logging
import os
import uvicorn


from database_Creation import connect_Database, test_database_connection
from load_data import main as load_gtfs_data
from a_gtfs import router as gtfs
from a_stops_fastapi import router as stops
from a_realtime import router as realtime
from a_routing_fastapi import router as routes
from a_algorithms import router as analysis
from a_mobility import router as mobility


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
   
    # Startup
    logger.info("Starting FastAPI application...")
    try:
        test_database_connection()
        logger.info("Database connection successful")
        logger.info("Loading GTFS data...")
        load_gtfs_data()
        logger.info("GTFS data loaded successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")

     
# Create FastAPI app
app = FastAPI(
    title="GTFS Route Planning API",
    description="Backend of project using GTFS data, PostGIS, and pgRouting",
    lifespan=lifespan,
    json_encoders={str: lambda v: v}
)

# Middleware to ensure UTF-8 encoding in responses
class UTF8ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if "application/json" in response.headers.get("content-type", ""):
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response

app.add_middleware(UTF8ResponseMiddleware)


# Include routers
app.include_router(gtfs, prefix="/gtfs")
app.include_router(stops, prefix="/stops")
app.include_router(realtime, prefix="/realtime")
app.include_router(routes, prefix="/routing")
app.include_router(analysis, prefix="/analysis")
app.include_router(mobility, prefix="/mobility")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/map")
def map_page():
    return FileResponse("template/index.html")

@app.get("/")
def root():
    return FileResponse("template/index.html")

if __name__ == "__main__":    
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
    )
