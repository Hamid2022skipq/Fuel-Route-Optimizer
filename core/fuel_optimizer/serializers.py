from rest_framework import serializers

class FuelStopSerializer(serializers.Serializer):
    """Defines the exact structure of a single fuel stop in the response."""
    name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price = serializers.FloatField()
    mile_marker = serializers.FloatField()
    distance_from_route = serializers.FloatField()

class RouteResponseSerializer(serializers.Serializer):
    """Defines the exact structure of the entire API response."""
    start_location = serializers.CharField()
    end_location = serializers.CharField()
    total_distance_miles = serializers.FloatField()
    estimated_drive_time_hours = serializers.FloatField()
    map_url = serializers.URLField()
    
    # We use a DictField here because the fuel_strategy is a nested 
    # dictionary containing both primitives and a list of FuelStopSerializers
    fuel_strategy = serializers.DictField() 

class RouteRequestSerializer(serializers.Serializer):
    """Validates the incoming query parameters."""
    start = serializers.CharField(required=True, help_text="Starting location (e.g., 'New York, NY')")
    end = serializers.CharField(required=True, help_text="Destination location (e.g., 'Los Angeles, CA')")