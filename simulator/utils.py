import random
from typing import Tuple

# Bengaluru hotspots (business + nightlife + tech + airport corridors)
HOTSPOTS = [
    (12.9716, 77.5946),  # MG Road / CBD
    (12.9352, 77.6245),  # Koramangala
    (12.9784, 77.6408),  # Indiranagar
    (12.9116, 77.6474),  # HSR Layout
    (12.9860, 77.7060),  # Whitefield
    (13.0358, 77.5970),  # Hebbal
    (12.9260, 77.6762),  # Bellandur
    (12.9141, 77.6100),  # Jayanagar
    (12.9908, 77.5389),  # Rajajinagar
    (13.1986, 77.7066),  # Airport corridor
]

# Wider city bounds (visual richness)
MIN_LAT, MAX_LAT = 12.82, 13.16
MIN_LON, MAX_LON = 77.42, 77.82


def generate_random_location() -> Tuple[float, float]:
    """
    80% hotspot clusters
    20% city-wide random spread
    """
    if random.random() < 0.80:
        base_lat, base_lon = random.choice(HOTSPOTS)
        lat = base_lat + random.uniform(-0.010, 0.010)
        lon = base_lon + random.uniform(-0.010, 0.010)
    else:
        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)

    return lat, lon


def move_driver(lat: float, lon: float):
    """
    Smooth roaming movement
    """
    nlat = lat + random.uniform(-0.0018, 0.0018)
    nlon = lon + random.uniform(-0.0018, 0.0018)

    nlat = max(MIN_LAT, min(MAX_LAT, nlat))
    nlon = max(MIN_LON, min(MAX_LON, nlon))

    return nlat, nlon