class StationFinder:
    """Responsibility: Find nearby fuel stations within a specified radius using a spatial index."""
    def __init__(self, df, tree, search_radius_miles: float):
        self.df = df
        self.tree = tree
        self.radius_degrees = search_radius_miles / 69.0  # Approximate conversion

    def find_nearby_stations(self, target_lat: float, target_lon: float) -> list[dict]:
        """Responsibility: Query the spatial index to find stations within the search radius."""
        indices = self.tree.query_ball_point([target_lat, target_lon], r=self.radius_degrees)
        stations = []
        
        for i in indices:
            station = self.df.iloc[i]
            stations.append({
                'name': station['name'],
                'city': station['city'],
                'state': station['state'],
                'price': float(station['price']),
                'lat': station['lat'],
                'lon': station['lon']
            })
        return stations