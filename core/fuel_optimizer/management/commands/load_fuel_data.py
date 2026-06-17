import os
import time
import logging
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Django management command to load and geocode fuel price data from a CSV file.
    
    Responsibilities:
        1. Load raw fuel price data from 'fuel-prices-for-be-assessment.csv'.
        2. Aggregate prices by City/State to minimize geocoding calls.
        3. Geocode each unique City/State to get latitude and longitude.
        4. Save the enriched data to 'fuel_prices_geocoded.csv' for use in the application.
    """
    
    help = 'Geocodes fuel prices CSV and saves a lightweight version for fast API lookups'

    def handle(self, *args, **kwargs):
        # Use Django's BASE_DIR for reliable path resolution regardless of where the command is run from
        input_csv = os.path.join(settings.BASE_DIR, 'fuel-prices-for-be-assessment.csv')
        output_csv = os.path.join(settings.BASE_DIR, 'fuel_prices_geocoded.csv')
        
        if not os.path.exists(input_csv):
            logger.error(f"CSV not found at {input_csv}")
            self.stdout.write(self.style.ERROR(f"CSV not found at {input_csv}"))
            return

        logger.info("Loading and aggregating CSV...")
        self.stdout.write("Loading and aggregating CSV...")
        
        df = pd.read_csv(input_csv)
        
        # Aggregate by City/State to get average price and minimize geocoding calls
        df['search_query'] = df['City'].str.strip() + ', ' + df['State'].str.strip()
        location_prices = df.groupby('search_query')['Retail Price'].mean().reset_index()
        
        geolocator = Nominatim(user_agent="django_fuel_optimizer_api")
        records = []
        
        total_locations = len(location_prices)
        logger.info(f"Geocoding {total_locations} unique locations (this may take a few minutes)...")
        self.stdout.write(f"Geocoding {total_locations} unique locations (this may take a few minutes)...")
        
        for index, row in location_prices.iterrows():
            try:
                location = geolocator.geocode(row['search_query'], country_codes='us', timeout=10)
                if location:
                    records.append({
                        'name': row['search_query'].split(',')[0].strip(),
                        'city': row['search_query'].split(',')[0].strip(),
                        'state': row['search_query'].split(',')[1].strip(),
                        'price': row['Retail Price'],
                        'lat': location.latitude,
                        'lon': location.longitude
                    })
                time.sleep(1.1) # Respect Nominatim's 1 request per second rate limit
                logger.info(f"Geocoded {row['search_query']} to {location.latitude}, {location.longitude}")
            except Exception as e:
                logger.warning(f"Failed to geocode {row['search_query']}: {e}")
                continue
                
        processed_df = pd.DataFrame(records)
        processed_df.to_csv(output_csv, index=False)
        
        success_msg = f"Successfully saved {len(processed_df)} locations to {output_csv}"
        logger.info(success_msg)
        self.stdout.write(self.style.SUCCESS(f"✅ {success_msg}"))