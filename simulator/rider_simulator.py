import time
import uuid
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location
from simulator.geofence import get_zone
from simulator.redis_client import redis_client

print("[INFO] Rider simulation started...")

try:
    while True:
        rider_id = str(uuid.uuid4())
        lat, lon = generate_random_location()
        zone = get_zone(lat, lon)

        redis_client.hset(
            f"rider:{rider_id}",
            mapping={
                "lat": lat,
                "lon": lon,
                "zone": zone,
                "timestamp": time.time()
            }
        )
        redis_client.expire(f"rider:{rider_id}", 120)

        time.sleep(3)

except KeyboardInterrupt:
    print("[STOP] Rider simulator stopped.")