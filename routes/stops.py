"""
Stops endpoints
GET /stops - List all stops (limited to 50)
GET /stops/nearby - Find stops near a location using PostGIS
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from db import execute_query, execute_query_one

logger = logging.getLogger(__name__)

router = APIRouter()


class StopResponse(BaseModel):
    """Stop data model"""
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    stop_code: Optional[str] = None
    stop_desc: Optional[str] = None


class StopsListResponse(BaseModel):
    """Response for stops list"""
    count: int
    limit: int
    stops: List[StopResponse]


class NearbyStopResponse(BaseModel):
    """Stop data with distance for nearby stops"""
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    distance_meters: float


class NearbyStopsResponse(BaseModel):
    """Response for nearby stops"""
    lat: float
    lon: float
    radius_meters: float
    count: int
    stops: List[NearbyStopResponse]


@router.get("/stops", response_model=StopsListResponse)
def get_stops(limit: int = Query(50, ge=1, le=1000)):
    """
    Get list of stops from GTFS stops table
    
    Args:
        limit: Number of stops to return (default: 50, max: 1000)
        
    Returns:
        StopsListResponse: List of stops with basic information
    """
    try:
        query = """
            SELECT 
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                stop_code,
                stop_desc
            FROM stops
            ORDER BY stop_id
            LIMIT %s
        """
        
        stops = execute_query(query, (limit,))
        
        if not stops:
            return StopsListResponse(count=0, limit=limit, stops=[])
        
        # Convert to response models
        stop_list = [
            StopResponse(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                stop_lat=float(row["stop_lat"]),
                stop_lon=float(row["stop_lon"]),
                stop_code=row.get("stop_code"),
                stop_desc=row.get("stop_desc")
            )
            for row in stops
        ]
        
        return StopsListResponse(count=len(stop_list), limit=limit, stops=stop_list)
        
    except Exception as e:
        logger.error(f"Error fetching stops: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stops: {str(e)}")


@router.get("/stops/nearby", response_model=NearbyStopsResponse)
def get_nearby_stops(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(500, ge=10, le=50000, description="Search radius in meters")
):
    """
    Find stops near a given location using PostGIS ST_DWithin
    
    Args:
        lat: Latitude of search center
        lon: Longitude of search center
        radius: Search radius in meters (default: 500, range: 10-50000)
        
    Returns:
        NearbyStopsResponse: List of stops within radius, sorted by distance
    """
    try:
        # Using PostGIS ST_DWithin for efficient spatial queries
        # The geometry is in SRID 4326 (WGS84)
        query = """
            SELECT 
                s.stop_id,
                s.stop_name,
                s.stop_lat,
                s.stop_lon,
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    s.geom
                ) AS distance_meters
            FROM stops s
            WHERE ST_DWithin(
                s.geom,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                %s,
                true  -- use spheroid for accurate Earth distance
            )
            ORDER BY distance_meters ASC
        """
        
        nearby_stops = execute_query(query, (lon, lat, lon, lat, radius))
        
        if not nearby_stops:
            return NearbyStopsResponse(
                lat=lat,
                lon=lon,
                radius_meters=radius,
                count=0,
                stops=[]
            )
        
        # Convert to response models
        stop_list = [
            NearbyStopResponse(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                stop_lat=float(row["stop_lat"]),
                stop_lon=float(row["stop_lon"]),
                distance_meters=float(row["distance_meters"])
            )
            for row in nearby_stops
        ]
        
        return NearbyStopsResponse(
            lat=lat,
            lon=lon,
            radius_meters=radius,
            count=len(stop_list),
            stops=stop_list
        )
        
    except Exception as e:
        logger.error(f"Error fetching nearby stops: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching nearby stops: {str(e)}")


@router.get("/stops/{stop_id}")
def get_stop_detail(stop_id: str):
    """
    Get detailed information about a specific stop
    
    Args:
        stop_id: The GTFS stop_id
        
    Returns:
        Stop detail including all available fields
    """
    try:
        query = """
            SELECT 
                stop_id,
                stop_code,
                stop_name,
                stop_desc,
                stop_lat,
                stop_lon,
                zone_id,
                stop_url,
                location_type,
                parent_station,
                stop_timezone,
                wheelchair_boarding,
                ST_AsGeoJSON(geom) AS geojson
            FROM stops
            WHERE stop_id = %s
        """
        
        stop = execute_query_one(query, (stop_id,))
        
        if not stop:
            raise HTTPException(status_code=404, detail=f"Stop {stop_id} not found")
        
        return {
            **dict(stop),
            "stop_lat": float(stop["stop_lat"]),
            "stop_lon": float(stop["stop_lon"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stop detail: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stop: {str(e)}")
