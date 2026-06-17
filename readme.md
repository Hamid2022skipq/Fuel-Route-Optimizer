# Fuel Route Optimizer API

A high-performance Django REST Framework (DRF) API that calculates the most cost-effective fuel stops for a cross-country trip. Given a start and end location within the USA, the API returns the optimal route, estimated drive time, a visual map link, and a list of recommended fuel stops based on real-time spatial data and retail fuel prices.

---

## 1. How to Run This Project

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package manager)
- The provided dataset: `fuel-prices-for-be-assessment.csv`

### Step-by-Step Setup

**1. Clone or download the project** and navigate into the root directory (where `manage.py` is located).

**2. Create and activate a virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```
**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Place the CSV file:**
Ensure `fuel-prices-for-be-assessment.csv` is placed in the **root directory** (the same folder as `manage.py`).

**5. Preprocess the Data (Crucial Step):**
The raw CSV lacks GPS coordinates. We must geocode the locations to build our in-memory spatial index. 
*(Note: This uses the free Nominatim API which is rate-limited to 1 request/second. This may take up to 1-2 hours depending on the dataset size, but it only needs to be run **once**).*
```bash
python manage.py load_fuel_data
```
*Wait until you see the success message: `Successfully saved X locations to fuel_prices_geocoded.csv`*

**6. Start the Django Server:**
```bash
python manage.py runserver
```

**7. Test the API:**
Open your browser, Postman, or cURL and hit the following endpoint:
```text
http://127.0.0.1:8000/api/optimal-route/?start=New York, NY&end=Los Angeles, CA
```

---

## 2. About & Tech Stack

### Who Made This?
Developed by **[Your Name/Team]** for the Backend Engineering Assessment. 

### What We Are Using
This project is built using a modern, service-oriented Python stack designed for maximum speed and minimal external API reliance:

- **Backend Framework:** Django & Django REST Framework (DRF)
- **Spatial Indexing & Math:** `SciPy` (specifically `scipy.spatial.KDTree`) and `Pandas`
- **Routing API:** [OSRM (Open Source Routing Machine)](http://router.project-osrm.org/) (Free, no API key required)
- **Geocoding API:** [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/) (Free, no API key required)
- **Frontend Mapping (Conceptual):** OpenStreetMap via Leaflet.js (The API returns a direct OSRM map URL for immediate visual routing)

---

## 3. Project Structure

The codebase strictly adheres to the **Single Responsibility Principle (SRP)**. The `views.py` file contains **zero** business logic. The heavy lifting is delegated to isolated, testable service classes.

```text
core/
├── manage.py
├── fuel-prices-for-be-assessment.csv   # Raw data
├── fuel_prices_geocoded.csv            # Generated preprocessed data
├── requirements.txt
└── fuel_optimizer/
    ├── apps.py                         # Loads KDTree into memory on startup
    ├── views.py                        # HTTP Orchestration only
    ├── serializers.py                  # DRF Input/Output validation
    ├── urls.py
    ├── services/                       # SRP Business Logic
    │   ├── data_loader.py              # Loads CSV & builds KDTree
    │   ├── geocoding.py                # Text to Lat/Lon (Nominatim)
    │   ├── routing.py                  # Fetches route (OSRM)
    │   ├── distance.py                 # Haversine & cumulative math
    │   ├── station_finder.py           # Queries KDTree for nearby stations
    │   ├── station_selector.py         # Filters & picks cheapest station
    │   ├── fuel_planner.py             # Orchestrates stop-finding logic
    │   └── cost_calculator.py          # Calculates total fuel cost
    └── management/
        └── commands/
            └── load_fuel_data.py       # Geocodes raw CSV.
```

---

## 4. API Response Structure

When you make a `GET` request to `/api/optimal-route/?start=...&end=...`, the API returns a highly structured JSON response. 

```json
{
    "start_location": "New York, NY",
    "end_location": "Los Angeles, CA",
    "total_distance_miles": 2789.45,
    "estimated_drive_time_hours": 40.12,
    "map_url": "https://map.project-osrm.org/?z=5&center=40.71,-74.00&route=40.71,-74.00;34.05,-118.24",
    "fuel_strategy": {
        "vehicle_mpg": 10.0,
        "max_range_miles": 500.0,
        "gallons_per_fillup": 50.0,
        "total_estimated_fuel_cost": 845.50,
        "recommended_stops": [
            {
                "name": "TA COUNCIL BLUFFS TRAVEL CENTER",
                "city": "Council Bluffs",
                "state": "IA",
                "price": 3.72,
                "mile_marker": 1150.2,
                "distance_from_route": 2.1
            },
            {
                "name": "LOVES TRAVEL STOP #173",
                "city": "Lawrence",
                "state": "KS",
                "price": 3.22,
                "mile_marker": 1650.5,
                "distance_from_route": 1.8
            }
        ]
    }
}
```

---

## 5. Architecture & Design Decisions

### Why is it so fast? (The KDTree Advantage)
Instead of querying a traditional database (like PostgreSQL/PostGIS) which incurs I/O latency, the `load_fuel_data` command geocodes the CSV *once* and saves it. When the Django server starts, the `FuelDataLoader` service reads this lightweight CSV into memory and builds a **SciPy KDTree**. 
- **Result:** Finding the nearest gas stations to any point on the route takes **microseconds** (O(log N) time complexity), making the API response nearly instantaneous.

### Strict API Call Limits
To ensure reliability and respect free-tier rate limits, the API is strictly constrained to a maximum of **3 external HTTP calls per request**:
1. **Nominatim:** Geocode `start` location.
2. **Nominatim:** Geocode `end` location.
3. **OSRM:** Fetch the driving route and polyline.
*All fuel station lookups and cost calculations are done locally in RAM.*

### Fuel Logic & Assumptions
- **Vehicle Specs:** 10 Miles Per Gallon (MPG), 500-mile maximum range (50-gallon tank).
- **Starting State:** The vehicle is assumed to start with a **full tank**.
- **Look-Ahead Strategy:** The algorithm looks **400 miles ahead** (leaving a 100-mile safety buffer) to find the cheapest gas.
- **Search Radius:** It searches for stations within a **15-mile radius** of the highway route.
- **Fill-up Logic:** At every recommended stop, the algorithm assumes the driver fills the entire 50-gallon tank to maximize the distance to the next stop.
- **"Gas Desert" Fallback:** If the route passes through a remote area with no stations within 15 miles, the algorithm gracefully falls back to the absolute closest station in the entire database to prevent the vehicle from running out of fuel.

### Visualizing the Route
The API response includes a `map_url` generated by OSRM. You can copy and paste this URL directly into your web browser to see an interactive map of the exact route, complete with start and end markers.
```