class CostCalculator:
    def calculate_total_cost(self, stops: list[dict], mpg: float, max_range_miles: float) -> float:
        """Responsibility: Calculate the total fuel cost for the planned stops."""
        tank_capacity_gallons = max_range_miles / mpg
        return sum(stop['price'] * tank_capacity_gallons for stop in stops)