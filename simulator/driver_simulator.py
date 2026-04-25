import time
import uuid
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location, move_driver
from simulator.geofence import get_zone
from simulator.redis_client import redis_client

# Stable for Render free tier
TARGET_DRIVERS = 300
TICK_SECONDS = 3
TTL_SECONDS = 90


def seed_driver(drivers: dict):
    driver_id = str(uuid.uuid4())
    lat, lon = generate_random_location()
    drivers[driver_id] = {
        "lat": lat,
        "lon": lon
    }


def run_driver_simulator():
    drivers = {}
    print("[INFO] Driver simulator started")

    # Initial pool
    for _ in range(TARGET_DRIVERS):
        seed_driver(drivers)

    while True:
        try:
            while len(drivers) < TARGET_DRIVERS:
                seed_driver(drivers)

            # Occasionally retire some drivers
            if len(drivers) > 100 and int(time.time()) % 15 == 0:
                remove_count = min(5, len(drivers))

                for did in list(drivers.keys())[:remove_count]:
                    drivers.pop(did, None)
                    redis_client.delete(f"driver:{did}")

            for did in list(drivers.keys()):
                lat = drivers[did]["lat"]
                lon = drivers[did]["lon"]

                lat, lon = move_driver(lat, lon)
                zone = get_zone(lat, lon)

                drivers[did]["lat"] = lat
                drivers[did]["lon"] = lon

                redis_client.hset(
                    f"driver:{did}",
                    mapping={
                        "lat": lat,
                        "lon": lon,
                        "zone": zone,
                        "timestamp": time.time()
                    }
                )

                redis_client.expire(
                    f"driver:{did}",
                    TTL_SECONDS
                )

            time.sleep(TICK_SECONDS)

        except Exception as e:
            print("Driver simulator error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_driver_simulator()