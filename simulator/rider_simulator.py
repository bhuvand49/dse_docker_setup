import time
import uuid
import sys
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location
from simulator.geofence import get_zone
from simulator.redis_client import redis_client

# Optimized for Render + Redis free tier
BASE_RIDERS_PER_TICK = 15
TICK_SECONDS = 3
TTL_SECONDS = 75


def current_multiplier():
    hour = time.localtime().tm_hour

    # Morning rush
    if 7 <= hour <= 10:
        return 1.6

    # Evening rush
    if 17 <= hour <= 22:
        return 1.8

    # Late night
    if hour >= 22 or hour <= 1:
        return 1.4

    return 1.0


def run_rider_simulator():
    print("[INFO] Rider simulator started")

    while True:
        try:
            multiplier = current_multiplier()
            riders_to_add = int(BASE_RIDERS_PER_TICK * multiplier)

            # Random spikes
            if random.random() < 0.08:
                riders_to_add += random.randint(8, 20)

            for _ in range(riders_to_add):
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

                redis_client.expire(
                    f"rider:{rider_id}",
                    TTL_SECONDS
                )

            time.sleep(TICK_SECONDS)

        except Exception as e:
            print("Rider simulator error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_rider_simulator()