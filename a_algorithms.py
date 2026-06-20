"""
FastAPI router for advanced pathfinding and network analysis features
done!
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from database_Creation import execute_query, connect_Database
import logging
import json
from Query_tables import get_metro_stations, get_metro_network_geojson, get_metro_shortest_path, get_metro_astar_path
from Query_working_algorithms import (
    get_tsp_selected_stops_query,
    get_tsp_order_query,
    get_full_network_query
)

from Query_extra import (
    get_top_routes_by_trip_count,
    get_route_with_stops
)


router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)

# ============================================================================
#  ALGORITHMS
# ============================================================================


@router.get("/network")
def full_network():
    network = get_full_network_query()
    return network

@router.get("/dijkstra")
def get_dijkstra_route(start: str = Query(..., description="Start metro stop ID"), end: str = Query(..., description="End metro stop ID")):
    try:
        # Get metro-only shortest path
        stops = get_metro_shortest_path(start, end)

        if not stops:
            raise HTTPException(status_code=404, detail="No metro path found between stops")

        # Build response with path data
        path = []
        total_cost = 0
        for stop in stops:
            path.append({
                "stop_id": stop["stop_id"],
                "stop_name": stop["stop_name"],
                "stop_lat": stop["stop_lat"],
                "stop_lon": stop["stop_lon"],
                "distance_from_start": stop.get("agg_cost", 0)
            })
            total_cost = stop.get("agg_cost", 0)

        return {
            "algorithm": "Dijkstra (Metro)",
            "path": path,
            "total_distance": total_cost,
            "hops": len(path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in Dijkstra metro route calculation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/astar")
def get_astar_route(start: str = Query(..., description="Start metro stop ID"), end: str = Query(..., description="End metro stop ID")):
    try:
        # Get metro-only A* path
        stops = get_metro_astar_path(start, end)

        if not stops:
            raise HTTPException(status_code=404, detail="No metro path found between stops")

        # Build response with path data
        path = []
        total_cost = 0
        for stop in stops:
            path.append({
                "stop_id": stop["stop_id"],
                "stop_name": stop["stop_name"],
                "stop_lat": stop["stop_lat"],
                "stop_lon": stop["stop_lon"],
                "distance_from_start": stop.get("agg_cost", 0)
            })
            total_cost = stop.get("agg_cost", 0)

        return {
            "algorithm": "A* (Metro)",
            "path": path,
            "total_distance": total_cost,
            "hops": len(path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in A* metro route calculation")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tsp")
def get_tsp_route(start_id: int, stop_ids: list[int] = Query(...)):
    conn = connect_Database()
    try:
        stops = get_tsp_selected_stops_query(stop_ids)
        if not stops:
            raise HTTPException(status_code=404, detail="No stops found")

        tsp_order = get_tsp_order_query(conn, stop_ids, start_id)

        return {
            "stops": stops,
            "order": tsp_order
        }
    finally:
        conn.close()



# ============================================================================
# NETWORK ANALYSIS
# ============================================================================

@router.get("/top-routes")
def top_routes(limit: int = Query(10, ge=1, le=100)):
    """
    Get top routes by trip count
    """
    routes = get_top_routes_by_trip_count(limit)
    if not routes:
        raise HTTPException(status_code=404, detail="No routes found")
    return {
        "top_routes": routes,
        "total_routes_returned": len(routes)
    }


@router.get("/route/{route_id}")
def route_details(route_id: str):
    """
    Get a specific route and all its stops in sequence
    """
    result = get_route_with_stops(route_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result




@router.get("/busiest-stops")
def busiest_stops(
    start_hour: int = Query(..., ge=0, le=23),
    end_hour: int = Query(..., ge=0, le=23)
):
    try:
        query = """
            SELECT
                s.stop_id,
                s.stop_name,
                s.stop_lat,
                s.stop_lon,
                COUNT(*) AS total_visits,
                COUNT(DISTINCT t.route_id) AS unique_routes
            FROM stop_times st
            JOIN stops s ON st.stop_id = s.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            WHERE CAST(SPLIT_PART(st.arrival_time, ':', 1) AS INTEGER) >= %s
              AND CAST(SPLIT_PART(st.arrival_time, ':', 1) AS INTEGER) < %s
            GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
            ORDER BY total_visits DESC
            LIMIT 20
        """
        rows = execute_query(query, (start_hour, end_hour))

        return {
            "time_range": f"{start_hour}:00 - {end_hour}:00",
            "busiest_stops": rows
        }

    except Exception as e:
        logger.exception("Error fetching busiest stops")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    logger = logging.getLogger(__name__)

def rows_to_feature_collection(rows):
    features = []

    for row in rows:
        geojson_text = row.get("geojson")
        if not geojson_text:
            continue

        geometry = json.loads(geojson_text)
        properties = {k: v for k, v in row.items() if k != "geojson"}

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/metro-stations")
def metro_stations():
    """
    Return metro stations only.
    Used to populate start/end dropdowns.
    """
    try:
        return get_metro_stations()
    except Exception as e:
        logger.exception("Error fetching metro stations")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metro-network")
def metro_network():
    """
    Return the full metro network as GeoJSON.
    Used to draw the metro network in gray on the map.
    """
    try:
        rows = get_metro_network_geojson()
        return rows_to_feature_collection(rows)
    except Exception as e:
        logger.exception("Error fetching metro network")
        raise HTTPException(status_code=500, detail=str(e))