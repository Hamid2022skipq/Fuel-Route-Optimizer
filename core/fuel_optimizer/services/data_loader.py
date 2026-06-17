import os
import logging
import pandas as pd

from scipy.spatial import KDTree

logger = logging.getLogger(__name__)

class FuelDataLoader:
    """Responsibility: Load geocoded fuel data into memory and build a spatial index for fast nearest-neighbor lookups."""
    df = None
    tree = None

    @classmethod
    def load(cls, csv_path: str):
        """Responsibility: Load CSV into memory and build the spatial index exactly once."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Geocoded CSV not found at {csv_path}")
        
        cls.df = pd.read_csv(csv_path)
        coordinates = cls.df[['lat', 'lon']].values
        logger.info(f"Building spatial index with {len(coordinates)} points")
        cls.tree = KDTree(coordinates)