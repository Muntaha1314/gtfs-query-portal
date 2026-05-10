"""
Example: Using the GTFS Route Planning API programmatically
This script demonstrates how to use the API with Python requests library
"""

import requests
import json
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api"


class GTFSRouteClient:
    """Simple client for GTFS Route Planning API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000/api)
        """
        self.base_url = base_url
    
    def get_stops(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of stops
        
        Args:
            limit: Number of stops to return
            
        Returns:
            List of stops
        """
        response = requests.get(
            f"{self.base_url}/stops",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()["stops"]
    
    def get_stop_detail(self, stop_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a stop
        
        Args:
            stop_id: The stop ID
            
        Returns:
            Stop details including geometry
        """
        response = requests.get(f"{self.base_url}/stops/{stop_id}")
        response.raise_for_status()
        return response.json()
    
    def get_nearby_stops(self, lat: float, lon: float, 
                        radius: float = 500) -> List[Dict[str, Any]]:
        """
        Find stops near a location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters (default: 500)
            
        Returns:
            List of nearby stops with distances
        """
        response = requests.get(
            f"{self.base_url}/stops/nearby",
            params={
                "lat": lat,
                "lon": lon,
                "radius": radius
            }
        )
        response.raise_for_status()
        return response.json()["stops"]
    
    def get_routes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of routes
        
        Args:
            limit: Number of routes to return
            
        Returns:
            List of routes
        """
        response = requests.get(
            f"{self.base_url}/routes",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()["routes"]
    
    def find_route(self, start_stop_id: str, end_stop_id: str) -> Dict[str, Any]:
        """
        Find a route between two stops
        
        Args:
            start_stop_id: Starting stop ID
            end_stop_id: Ending stop ID
            
        Returns:
            Route information with path and distance
        """
        response = requests.get(
            f"{self.base_url}/route",
            params={
                "start": start_stop_id,
                "end": end_stop_id
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_route_geometry(self, route_id: str) -> Dict[str, Any]:
        """
        Get route geometry as GeoJSON
        
        Args:
            route_id: The route ID
            
        Returns:
            GeoJSON FeatureCollection with route shapes and stops
        """
        response = requests.get(f"{self.base_url}/route-geometry/{route_id}")
        response.raise_for_status()
        return response.json()


# Example usage
def example_basic_usage():
    """Basic usage example"""
    print("="*70)
    print("GTFS Route Planning API - Basic Usage Example")
    print("="*70)
    print()
    
    # Initialize client
    client = GTFSRouteClient()
    
    # 1. Get stops
    print("1. Getting first 5 stops...")
    try:
        stops = client.get_stops(limit=5)
        for i, stop in enumerate(stops, 1):
            print(f"   {i}. {stop['stop_name']} ({stop['stop_id']})")
            print(f"      Location: {stop['stop_lat']}, {stop['stop_lon']}")
        
        if stops:
            first_stop_id = stops[0]['stop_id']
            print()
            
            # 2. Get stop detail
            print(f"2. Getting details for stop {first_stop_id}...")
            stop_detail = client.get_stop_detail(first_stop_id)
            print(f"   Name: {stop_detail.get('stop_name')}")
            print(f"   Code: {stop_detail.get('stop_code')}")
            print(f"   Description: {stop_detail.get('stop_desc', 'N/A')}")
            print(f"   Wheelchair accessible: {stop_detail.get('wheelchair_boarding')}")
            print()
    
    except Exception as e:
        print(f"   Error: {e}")
        print()
    
    # 3. Get nearby stops
    print("3. Finding stops near downtown (40.7128, -74.0060) within 1000m...")
    try:
        nearby = client.get_nearby_stops(
            lat=40.7128,
            lon=-74.0060,
            radius=1000
        )
        print(f"   Found {len(nearby)} stops:")
        for i, stop in enumerate(nearby[:5], 1):
            print(f"   {i}. {stop['stop_name']} - {stop['distance_meters']:.0f}m away")
        
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()
    
    # 4. Get routes
    print("4. Getting first 5 routes...")
    try:
        routes = client.get_routes(limit=5)
        for i, route in enumerate(routes, 1):
            print(f"   {i}. Route {route['route_short_name']}: {route['route_long_name']}")
        
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()


def example_route_planning():
    """Route planning example"""
    print("="*70)
    print("GTFS Route Planning API - Route Planning Example")
    print("="*70)
    print()
    
    client = GTFSRouteClient()
    
    # Get nearby stops to use for routing
    print("Finding nearby stops to plan route...")
    try:
        nearby = client.get_nearby_stops(
            lat=40.7128,
            lon=-74.0060,
            radius=2000
        )
        
        if len(nearby) >= 2:
            start_stop = nearby[0]
            end_stop = nearby[1]
            
            print(f"Planning route from:")
            print(f"  Start: {start_stop['stop_name']} ({start_stop['stop_id']})")
            print(f"  End:   {end_stop['stop_name']} ({end_stop['stop_id']})")
            print()
            
            # Find route
            print("Searching for route...")
            route = client.find_route(
                start_stop['stop_id'],
                end_stop['stop_id']
            )
            
            if route['path_found']:
                print(f"✓ Route found!")
                print(f"  Total stops: {route['total_stops']}")
                print(f"  Distance: {route['distance_meters']:,.0f}m ({route['distance_meters']/1000:.1f}km)")
                print()
                print("  Path:")
                for i, stop in enumerate(route['path'][:10], 1):
                    print(f"    {i}. {stop['stop_name']}")
                
                if len(route['path']) > 10:
                    print(f"    ... and {len(route['path']) - 10} more stops")
            else:
                print("✗ No direct route found between these stops")
            
            print()
        else:
            print(f"Not enough stops found ({len(nearby)}) to plan route")
            
    except Exception as e:
        print(f"Error: {e}")
        print()


def example_route_geometry():
    """Route geometry visualization example"""
    print("="*70)
    print("GTFS Route Planning API - Route Geometry Example")
    print("="*70)
    print()
    
    client = GTFSRouteClient()
    
    # Get first route
    print("Getting first available route...")
    try:
        routes = client.get_routes(limit=1)
        
        if routes:
            route = routes[0]
            route_id = route['route_id']
            
            print(f"Route: {route['route_short_name']} - {route['route_long_name']}")
            print()
            
            # Get geometry
            print(f"Getting geometry for route {route_id}...")
            geojson = client.get_route_geometry(route_id)
            
            features = geojson['features']
            shape_features = [f for f in features if f['properties']['type'] == 'route_shape']
            stop_features = [f for f in features if f['properties']['type'] == 'stop']
            
            print(f"✓ Retrieved {len(shape_features)} shapes and {len(stop_features)} stops")
            print()
            print("GeoJSON structure:")
            print(f"  - Type: {geojson['type']}")
            print(f"  - Route ID: {geojson['properties']['route_id']}")
            print(f"  - Route Color: {geojson['properties']['route_color']}")
            print(f"  - Features: {len(features)}")
            print()
            print("This GeoJSON can be directly used with Leaflet or other mapping libraries")
            print()
            
            # Show sample coordinate
            if shape_features and shape_features[0]['geometry']['coordinates']:
                sample_coords = shape_features[0]['geometry']['coordinates'][0]
                print(f"Sample coordinate: {sample_coords}")
        else:
            print("No routes found")
            
    except Exception as e:
        print(f"Error: {e}")
        print()


def example_batch_processing():
    """Batch processing example"""
    print("="*70)
    print("GTFS Route Planning API - Batch Processing Example")
    print("="*70)
    print()
    
    client = GTFSRouteClient()
    
    # Define locations to search
    locations = [
        {"name": "Downtown", "lat": 40.7128, "lon": -74.0060},
        {"name": "Midtown", "lat": 40.7580, "lon": -73.9855},
        {"name": "Uptown", "lat": 40.7829, "lon": -73.9654},
    ]
    
    print("Searching for stops near multiple locations (500m radius)...")
    print()
    
    all_results = {}
    
    for location in locations:
        try:
            print(f"🔍 Searching near {location['name']}...")
            stops = client.get_nearby_stops(
                lat=location['lat'],
                lon=location['lon'],
                radius=500
            )
            all_results[location['name']] = stops
            print(f"   Found {len(stops)} stops")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    print()
    print("Summary:")
    for location_name, stops in all_results.items():
        print(f"  {location_name}: {len(stops)} stops")
    print()
    
    # Find total unique stops
    all_stops = []
    for stops in all_results.values():
        all_stops.extend([s['stop_id'] for s in stops])
    
    unique_stops = len(set(all_stops))
    print(f"Total unique stops across all locations: {unique_stops}")


if __name__ == "__main__":
    import sys
    
    print("\n")
    
    if len(sys.argv) > 1:
        example = sys.argv[1].lower()
        
        if example == "basic":
            example_basic_usage()
        elif example == "routing":
            example_route_planning()
        elif example == "geometry":
            example_route_geometry()
        elif example == "batch":
            example_batch_processing()
        else:
            print(f"Unknown example: {example}")
            print()
            print("Available examples:")
            print("  python api_examples.py basic       - Basic usage")
            print("  python api_examples.py routing     - Route planning")
            print("  python api_examples.py geometry    - Route geometry")
            print("  python api_examples.py batch       - Batch processing")
    else:
        # Run all examples
        example_basic_usage()
        example_route_planning()
        example_route_geometry()
        example_batch_processing()
        
        print("="*70)
        print("Examples complete!")
        print()
        print("To run individual examples:")
        print("  python api_examples.py basic")
        print("  python api_examples.py routing")
        print("  python api_examples.py geometry")
        print("  python api_examples.py batch")
        print("="*70)
        print()
