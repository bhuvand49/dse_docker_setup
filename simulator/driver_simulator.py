import time
import uuid
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from simulator.utils import generate_random_location, move_driver
from simulator.geofence import get_zone
from simulator.redis_client import redis_client


TARGET_DRIVERS = 900        # rich live map
TICK_SECONDS = 1.5         # faster updates
TTL_SECONDS = 90           # auto cleanup


def seed_driver(drivers: dict):
    driver_id = str(uuid.uuid4())
    lat, lon = generate_random_location()
    drivers[driver_id] = {"lat": lat, "lon": lon}


def run_driver_simulator():
    drivers = {}
    print("[INFO] Premium driver simulator started")

    # Initial seed
    for _ in range(TARGET_DRIVERS):
        seed_driver(drivers)

    while True:
        try:
            # maintain pool size
            while len(drivers) < TARGET_DRIVERS:
                seed_driver(drivers)

            # randomly retire a few drivers
            if len(drivers) > 100 and time.time() % 10 < 1:
                retire_count = min(8, len(drivers))
                for did in list(drivers.keys())[:retire_count]:
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
                redis_client.expire(f"driver:{did}", TTL_SECONDS)

            time.sleep(TICK_SECONDS)

        except Exception as e:
            print("Premium driver simulator error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_driver_simulator()