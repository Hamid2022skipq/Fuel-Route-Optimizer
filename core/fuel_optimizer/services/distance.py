import math
import logging

logger = logging.getLogger(__name__)

class DistanceCalculator:
    """Responsibility: Calculate cumulative mile markers for a list of route points."""

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance in miles between two points on the Earth."""
        R = 3958.8  # Earth radius in miles
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def calculate_cumulative_distances(self, route_points: list[tuple[float, float]]) -> list[float]:
        """Calculate cumulative distances along the route points."""
        distances = [0.0]
        current_cumulative = 0.0
        
        for i in range(1, len(route_points)):
            prev_pt = route_points[i-1]
            curr_pt = route_points[i]
            current_cumulative += self._haversine(prev_pt[0], prev_pt[1], curr_pt[0], curr_pt[1])
            distances.append(current_cumulative)
            logger.info(f"Calculated distance from {prev_pt} to {curr_pt}: {distances[-1]} miles")
        return distances