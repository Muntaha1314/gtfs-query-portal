"""
FastAPI Backend for GTFS Spatial Route Planning System
Connects to PostgreSQL with PostGIS and pgRouting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from routes.stops import router as stops_router
from routes.routing import router as routing_router
from db import test_database_connection

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
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")


# Create FastAPI app
app = FastAPI(
    title="GTFS Route Planning API",
    description="Spatial route planning backend using GTFS data, PostGIS, and pgRouting",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific frontend URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stops_router, prefix="/api", tags=["Stops"])
app.include_router(routing_router, prefix="/api", tags=["Routing"])


@app.get("/", tags=["Health"])
def root():
    """Root endpoint - API information"""
    return {
        "message": "GTFS Spatial Route Planning API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    try:
        test_database_connection()
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
