"""
Routing endpoints
GET /routes - List transit routes
GET /route - Find shortest path between stops using pgRouting
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from db import execute_query, execute_query_one

logger = logging.getLogger(__name__)

router = APIRouter()


class RouteResponse(BaseModel):
    """Transit route data model"""
    route_id: str
    route_short_name: Optional[str] = None
    route_long_name: Optional[str] = None
    route_type: Optional[int] = None
    agency_id: Optional[str] = None
    route_color: Optional[str] = None


class RoutesListResponse(BaseModel):
    """Response for routes list"""
    count: int
    routes: List[RouteResponse]


class PathNode(BaseModel):
    """Node in a route path"""
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    sequence: int


class RoutingResponse(BaseModel):
    """Response for route path between two stops"""
    start_stop_id: str
    end_stop_id: str
    path_found: bool
    path: List[PathNode] = []
    total_stops: int = 0
    distance_meters: Optional[float] = None


@router.get("/routes", response_model=RoutesListResponse)
def get_routes(limit: int = Query(100, ge=1, le=1000)):
    """
    Get list of transit routes
    
    Args:
        limit: Number of routes to return (default: 100, max: 1000)
        
    Returns:
        RoutesListResponse: List of routes with basic information
    """
    try:
        query = """
            SELECT 
                route_id,
                route_short_name,
                route_long_name,
                route_type,
                agency_id,
                route_color,
                COUNT(DISTINCT t.trip_id) as trip_count
            FROM routes r
            LEFT JOIN trips t ON r.route_id = t.route_id
            GROUP BY r.route_id
            ORDER BY route_short_name
            LIMIT %s
        """
        
        routes = execute_query(query, (limit,))
        
        if not routes:
            return RoutesListResponse(count=0, routes=[])
        
        route_list = [
            RouteResponse(
                route_id=row["route_id"],
                route_short_name=row.get("route_short_name"),
                route_long_name=row.get("route_long_name"),
                route_type=row.get("route_type"),
                agency_id=row.get("agency_id"),
                route_color=row.get("route_color")
            )
            for row in routes
        ]
        
        return RoutesListResponse(count=len(route_list), routes=route_list)
        
    except Exception as e:
        logger.error(f"Error fetching routes: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching routes: {str(e)}")


@router.get("/route", response_model=RoutingResponse)
def find_route(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID"),
    exclude_walk: bool = Query(True, description="Exclude walking transfers")
):
    """
    Find a route path between two stops using stop_times connections
    
    For a real pgRouting implementation with network graph, ensure an edges table
    exists with proper topology. This endpoint uses GTFS stop_times for connections.
    
    Args:
        start: Start stop ID
        end: End stop ID
        exclude_walk: Whether to exclude walking transfers (default: True)
        
    Returns:
        RoutingResponse: Path from start to end stop with coordinates
    """
    try:
        # Validate that both stops exist
        start_check = execute_query_one(
            "SELECT stop_id, stop_name FROM stops WHERE stop_id = %s",
            (start,)
        )
        end_check = execute_query_one(
            "SELECT stop_id, stop_name FROM stops WHERE stop_id = %s",
            (end,)
        )
        
        if not start_check:
            raise HTTPException(status_code=404, detail=f"Start stop {start} not found")
        if not end_check:
            raise HTTPException(status_code=404, detail=f"End stop {end} not found")
        
        # For GTFS data without a pre-built network graph, we'll find connected routes
        # This query finds all trips that serve both stops
        query = """
            WITH common_trips AS (
                SELECT DISTINCT st1.trip_id
                FROM stop_times st1
                JOIN stop_times st2 ON st1.trip_id = st2.trip_id
                WHERE st1.stop_id = %s
                  AND st2.stop_id = %s
                  AND st1.stop_sequence < st2.stop_sequence
            )
            SELECT 
                s.stop_id,
                s.stop_name,
                s.stop_lat,
                s.stop_lon,
                st.stop_sequence
            FROM common_trips ct
            JOIN stop_times st ON ct.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st.stop_sequence BETWEEN 
                (SELECT stop_sequence FROM stop_times WHERE trip_id IN (SELECT trip_id FROM common_trips) AND stop_id = %s LIMIT 1)
                AND 
                (SELECT stop_sequence FROM stop_times WHERE trip_id IN (SELECT trip_id FROM common_trips) AND stop_id = %s LIMIT 1)
            ORDER BY st.stop_sequence
            LIMIT 100
        """
        
        path_stops = execute_query(query, (start, end, start, end))
        
        if not path_stops:
            # No direct common trip, return basic response
            return RoutingResponse(
                start_stop_id=start,
                end_stop_id=end,
                path_found=False,
                path=[
                    PathNode(
                        stop_id=start,
                        stop_name=start_check["stop_name"],
                        stop_lat=float(start_check["stop_lat"]),
                        stop_lon=float(start_check["stop_lon"]),
                        sequence=0
                    )
                ],
                total_stops=1
            )
        
        # Calculate total distance using PostGIS
        distance_query = """
            SELECT ST_Distance(
                s1.geom,
                s2.geom,
                true  -- use spheroid for accurate Earth distance
            ) as distance_meters
            FROM stops s1, stops s2
            WHERE s1.stop_id = %s AND s2.stop_id = %s
        """
        
        distance_result = execute_query_one(distance_query, (start, end))
        total_distance = float(distance_result["distance_meters"]) if distance_result else None
        
        # Convert to response models
        path_nodes = [
            PathNode(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                stop_lat=float(row["stop_lat"]),
                stop_lon=float(row["stop_lon"]),
                sequence=int(row["stop_sequence"])
            )
            for row in path_stops
        ]
        
        return RoutingResponse(
            start_stop_id=start,
            end_stop_id=end,
            path_found=True,
            path=path_nodes,
            total_stops=len(path_nodes),
            distance_meters=total_distance
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding route: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding route: {str(e)}")


@router.get("/route-geometry/{route_id}")
def get_route_geometry(route_id: str):
    """
    Get the geometry of all shapes for a specific route as GeoJSON
    
    Args:
        route_id: The GTFS route_id
        
    Returns:
        GeoJSON FeatureCollection with route shapes and stop locations
    """
    try:
        # Get route info
        route_query = """
            SELECT 
                route_id,
                route_short_name,
                route_long_name,
                route_color
            FROM routes
            WHERE route_id = %s
        """
        
        route = execute_query_one(route_query, (route_id,))
        if not route:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
        
        # Get route shapes as GeoJSON
        shapes_query = """
            SELECT 
                t.shape_id,
                ST_AsGeoJSON(sg.geom) AS geometry
            FROM trips t
            JOIN shape_geoms sg ON t.shape_id = sg.shape_id
            WHERE t.route_id = %s
            GROUP BY t.shape_id, sg.geom
        """
        
        shapes = execute_query(shapes_query, (route_id,))
        
        # Get all stops for this route
        stops_query = """
            SELECT DISTINCT
                s.stop_id,
                s.stop_name,
                s.stop_lat,
                s.stop_lon,
                ST_AsGeoJSON(s.geom) AS geometry
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            WHERE t.route_id = %s
            ORDER BY s.stop_name
        """
        
        stops = execute_query(stops_query, (route_id,))
        
        # Build GeoJSON response
        features = []
        
        # Add shapes
        for shape in shapes:
            features.append({
                "type": "Feature",
                "geometry": eval(shape["geometry"]) if isinstance(shape["geometry"], str) else shape["geometry"],
                "properties": {
                    "type": "route_shape",
                    "shape_id": shape["shape_id"]
                }
            })
        
        # Add stops
        for stop in stops:
            features.append({
                "type": "Feature",
                "geometry": eval(stop["geometry"]) if isinstance(stop["geometry"], str) else stop["geometry"],
                "properties": {
                    "type": "stop",
                    "stop_id": stop["stop_id"],
                    "stop_name": stop["stop_name"]
                }
            })
        
        return {
            "type": "FeatureCollection",
            "properties": {
                "route_id": route["route_id"],
                "route_short_name": route.get("route_short_name"),
                "route_long_name": route.get("route_long_name"),
                "route_color": route.get("route_color")
            },
            "features": features
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route geometry: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting route geometry: {str(e)}")
