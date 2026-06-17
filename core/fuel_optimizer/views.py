import os
import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.data_loader import FuelDataLoader
from .services.geocoding import GeocodingService
from .services.routing import RoutingService
from .services.fuel_planner import FuelPlanner
from .services.cost_calculator import CostCalculator
from .serializers import RouteRequestSerializer, RouteResponseSerializer

loggers = logging.getLogger(__name__)

class OptimalRouteView(APIView):
    """  
        Responsibility: Handle GET requests to compute the optimal fuel stops along a route.
    
        This view orchestrates the following steps:
            1. Validate input using RouteRequestSerializer.
            2. Geocode start and end locations using GeocodingService.
            3. Fetch route geometry and metrics using RoutingService.
            4. Plan optimal fuel stops using FuelPlanner.
            5. Calculate total fuel cost using CostCalculator.
            6. Format and return the response using RouteResponseSerializer.
    """
    def __init__(self, **kwargs):

        """ Responsibility: Initialize the view with necessary services and load fuel data once per process.
            Steps:
                1. Initialize GeocodingService and RoutingService.
                2. Load fuel price data from CSV and prepare for fast lookups.
        """

        super().__init__(**kwargs)
        # Initialize services (dependencies injected or instantiated)
        self.geocoding_service = GeocodingService()
        self.routing_service = RoutingService()
        
        # Load data once per process
        csv_path = os.path.join(settings.BASE_DIR, 'fuel_prices_geocoded.csv')
        FuelDataLoader.load(csv_path)
        
        self.planner = FuelPlanner(
            df=FuelDataLoader.df,
            tree=FuelDataLoader.tree,
            max_range_miles=500.0,
            search_radius_miles=15.0
        )
        self.cost_calculator = CostCalculator()

    def get(self, request):

        """ Responsibility: Handle GET requests to compute the optimal fuel stops along a route.
            Steps:
                1. Validate input using RouteRequestSerializer.
                2. Geocode start and end locations using GeocodingService.
                3. Fetch route geometry and metrics using RoutingService.
                4. Plan optimal fuel stops using FuelPlanner.
                5. Calculate total fuel cost using CostCalculator.
                6. Format and return the response using RouteResponseSerializer.
        """
        # 1. VALIDATE INPUT using the Serializer (No Model needed)
        request_serializer = RouteRequestSerializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        
        start_loc = request_serializer.validated_data['start']
        end_loc = request_serializer.validated_data['end']

        try:
            # 1. Geocode
            start_lat, start_lon = self.geocoding_service.geocode(start_loc)
            end_lat, end_lon = self.geocoding_service.geocode(end_loc)
            loggers.info(f"Geocoded start: {start_loc} -> ({start_lat}, {start_lon}), end: {end_loc} -> ({end_lat}, {end_lon})")
            
            # 2. Route
            route_data = self.routing_service.get_route(start_lat, start_lon, end_lat, end_lon)
            loggers.info(f"Route data: {route_data['distance_miles']} miles, {route_data['duration_hours']} hours")
            
            # 3. Plan Stops
            optimal_stops = self.planner.plan_stops(route_data['points'], route_data['distance_miles'])
            loggers.info(f"Planned {len(optimal_stops)} optimal fuel stops along the route")
            
            # 4. Calculate Cost
            total_cost = self.cost_calculator.calculate_total_cost(optimal_stops, mpg=10.0, max_range_miles=500.0)
            loggers.info(f"Total estimated fuel cost for the trip: ${total_cost:.2f}")

            # 5. Format Response
            map_url = f"https://map.project-osrm.org/?z=5&center={start_lat},{start_lon}&route={start_lat},{start_lon};{end_lat},{end_lon}"
            loggers.info(f"Map URL: {map_url}")
            
            response_data = {
                "start_location": start_loc,
                "end_location": end_loc,
                "total_distance_miles": round(route_data['distance_miles'], 2),
                "estimated_drive_time_hours": round(route_data['duration_hours'], 2),
                "map_url": map_url,
                "fuel_strategy": {
                    "vehicle_mpg": 10.0,
                    "max_range_miles": 500.0,
                    "gallons_per_fillup": 50.0,
                    "total_estimated_fuel_cost": round(total_cost, 2),
                    "recommended_stops": optimal_stops # List of dicts matching FuelStopSerializer
                }
            }
            
            # 3. FORMAT OUTPUT using the Serializer
            response_serializer = RouteResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
