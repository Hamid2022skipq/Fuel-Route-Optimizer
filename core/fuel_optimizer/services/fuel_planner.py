# fuel_optimizer/services/fuel_planner.py
from .distance import DistanceCalculator
from .station_finder import StationFinder

class FuelPlanner:
    """
        Responsibility: Plan optimal fuel stops along a route based on vehicle range, fuel station locations, and prices.
        Steps:
                1. Calculate cumulative distances along the route.
                2. Iteratively determine target points along the route based on max range and safety buffer.
                3. Use StationFinder to locate nearby stations at each target point.
                4. Filter and select the best station using price and forward progress criteria.
                5. Handle edge cases with fallback logic to ensure a station is always selected.
    """
    def __init__(self, df, tree, max_range_miles: float, search_radius_miles: float):
        """ 
            Responsibility: Initialize the planner with necessary data and parameters.
            Steps:
                1. Store max range and calculate safety buffer.
                2. Initialize StationFinder with fuel station data and spatial index.
                3. Initialize DistanceCalculator for distance computations. 
        """
        self.max_range = max_range_miles
        self.safety_buffer = max_range_miles * 0.2  # Look ahead 80% of range
        self.finder = StationFinder(df, tree, search_radius_miles)
        self.distance_calc = DistanceCalculator()

    def plan_stops(self, route_points: list[tuple[float, float]], total_miles: float) -> list[dict]:
        """
            Responsibility: Main method to plan fuel stops along the route.
            Steps:
                1. Calculate cumulative distances for the route points.
                2. Initialize current mile marker and empty stops list.
                3. Loop until we reach the end of the route:
                    a. Determine target mile marker based on max range and safety buffer.
                    b. Locate target coordinates on the route corresponding to the target mile marker.
                    c. Find nearby stations using StationFinder.
                    d. Filter and select the best station based on price and forward progress.
                    e. Append selected station to stops list and advance current mile marker.
                4. Return the list of planned stops.
        """
        cumulative_distances = self.distance_calc.calculate_cumulative_distances(route_points)
        stops = []
        current_mile = 0.0

        while current_mile < total_miles:
            target_mile = min(current_mile + (self.max_range - self.safety_buffer), total_miles)
            
            # Responsibility: Locate target coordinates
            route_idx, target_lat, target_lon, route_mile = self._locate_target_point(
                route_points, cumulative_distances, target_mile
            )
            
            # Responsibility: Find raw candidates
            raw_candidates = self.finder.find_nearby_stations(target_lat, target_lon)
            
            # Responsibility: Filter and select
            best_stop = self._select_best_stop(raw_candidates, current_mile, route_mile, target_lat, target_lon)
            
            stops.append(best_stop)
            
            # Advance current mile marker, but ensure we always move forward to prevent infinite loops
            if best_stop['mile_marker'] > current_mile:
                current_mile = best_stop['mile_marker']
            else:
                current_mile += 50.0  # Force advance if we are stuck at the exact end of the route

            # Safety break to prevent infinite loops
            if len(stops) > 20: 
                break

        return stops

    def _locate_target_point(self, points, distances, target_mile):
        """Responsibility: Find the route point closest to the target mile marker."""
        idx = min(range(len(distances)), key=lambda i: abs(distances[i] - target_mile))
        return idx, points[idx][0], points[idx][1], distances[idx]

    def _select_best_stop(self, candidates, current_mile, route_mile, target_lat, target_lon):
        """Responsibility: Select the best fuel station from candidates based on price and forward progress."""
        # 1. Filter for forward progress
        forward_candidates = [
            {**c, 'mile_marker': route_mile, 'distance_from_route': self.distance_calc._haversine(target_lat, target_lon, c['lat'], c['lon'])}
            for c in candidates if route_mile > current_mile
        ]

        if forward_candidates:
            return min(forward_candidates, key=lambda x: x['price'])
        
        # 2. If no forward candidates, check if we have ANY candidates in the local radius
        if candidates:
            closest = min(candidates, key=lambda x: self.distance_calc._haversine(target_lat, target_lon, x['lat'], x['lon']))
            return {
                **closest, 
                'mile_marker': route_mile, 
                'distance_from_route': self.distance_calc._haversine(target_lat, target_lon, closest['lat'], closest['lon']),
                'is_fallback': True
            }
        
        # 3. GLOBAL FALLBACK: If NO candidates at all (gas desert), find the absolute closest station in the entire DB
        distance, closest_idx = self.finder.tree.query([target_lat, target_lon])
        closest_station = self.finder.df.iloc[closest_idx]
        
        return {
            'name': closest_station['name'],
            'city': closest_station['city'],
            'state': closest_station['state'],
            'price': float(closest_station['price']),
            'lat': float(closest_station['lat']),
            'lon': float(closest_station['lon']),
            'mile_marker': route_mile,
            'distance_from_route': float(distance) * 69.0, # rough degrees-to-miles conversion
            'is_fallback': True
        }