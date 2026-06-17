import requests
import polyline
import logging

logger = logging.getLogger(__name__)

class RoutingService:

    """Responsibility: Fetch route geometry and metrics from the OSRM API."""

    def get_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=polyline"
        logger.info(f"Fetching route from {start_lat}, {start_lon} to {end_lat}, {end_lon}")
        
        response = requests.get(url)
        data = response.json()
        
        if data.get('code') != 'Ok':
            logger.error("Routing API failed to find a route")
            raise ValueError("Routing API failed to find a route")
            
        route = data['routes'][0]
        logger.info(f"Route fetched: {route['distance']} meters, {route['duration']} seconds") 
        return {
            'distance_miles': route['distance'] / 1609.34,
            'duration_hours': route['duration'] / 3600,
            'points': polyline.decode(route['geometry'])
        }