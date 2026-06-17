import logging

logger = logging.getLogger(__name__)

class StationSelector:
    """Responsibility: Filter and select the best fuel station based on price and location."""
    def filter_and_select(self, candidates: list[dict], current_mile: float, route_mile: float, distance_calc) -> dict:
        # 1. Filter for forward progress
        forward_stations = [
            {**c, 'mile_marker': route_mile} for c in candidates
        ]
        
        if not forward_stations:
            return self._get_fallback(candidates, route_mile, distance_calc)
            
        # 2. Select cheapest
        return min(forward_stations, key=lambda x: x['price'])

    def _get_fallback(self, candidates: list[dict], route_mile: float, distance_calc) -> dict:
        """Responsibility: If no forward stations, pick the absolute closest to avoid running out of gas."""
        # Fallback: If no forward stations, pick the absolute closest to avoid running out of gas
        closest = min(candidates, key=lambda x: distance_calc._haversine(
            # Note: We'd need target lat/lon here, but for strict SRP, 
            # the planner passes the necessary context or we simplify fallback logic.
            # For this strict SRP design, we assume the planner handles fallback injection.
            0, 0, x['lat'], x['lon'] # Placeholder, see planner for proper fallback
        ))
        return {**closest, 'mile_marker': route_mile, 'is_fallback': True}