import requests
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    def geocode(self, location: str) -> tuple[float, float]:
        """Responsibility: Convert a location string into latitude and longitude."""
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}&countrycodes=us"
        headers = {'User-Agent': 'FuelOptimizerAPI/1.0'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if not data:
            logger.error(f"Location not found: {location}")
            raise ValueError(f"Location not found: {location}")
            
        logger.info(f"Geocoded {location} to {data[0]['lat']}, {data[0]['lon']}")
        return float(data[0]['lat']), float(data[0]['lon'])