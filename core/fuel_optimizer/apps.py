import os
import pandas as pd
import logging

from scipy.spatial import KDTree

from django.apps import AppConfig

logger = logging.getLogger(__name__)

class FuelOptimizerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fuel_optimizer'

    def ready(self):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fuel_prices_geocoded.csv')
        if os.path.exists(csv_path):
            self.df = pd.read_csv(csv_path)
            self.coordinates = self.df[['lat', 'lon']].values
            self.tree = KDTree(self.coordinates)
            logger.info(f"Loaded {len(self.df)} fuel stations into memory KDTree.")
        else:
            logger.warning("fuel_prices_geocoded.csv not found. Run 'python manage.py load_fuel_data' first.")
            self.df = None
            self.tree = None