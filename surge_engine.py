import time
import random

from simulator.redis_client import redis_client
from ml.predictor import predict_surge, rule_based_surge

# Lower load / stable updates
SURGE_INTERVAL = 5


def fetch_entities(prefix):
    rows = []

    for key in redis_client.scan_iter(f"{prefix}:*"):
        item = redis_client.hgetall(key)
        if item:
            rows.append(item)

    return rows


def group_by_zone(rows):
    grouped = {}

    for row in rows:
        zone = row.get("zone")
        if zone:
            grouped[zone] = grouped.get(zone, 0) + 1

    return grouped


def calculate(drivers, riders, zone):
    rule = rule_based_surge(drivers, riders)
    ml = predict_surge(drivers, riders, zone)

    # Balanced blend
    final = (0.55 * rule) + (0.45 * ml)

    # Demand pressure
    if riders > drivers:
        gap = riders - drivers
        final += min(gap * 0.04, 1.4)

    # Light randomness
    final += random.uniform(-0.05, 0.10)

    # Smooth previous value
    prev = redis_client.hget(
        f"surge:{zone}",
        "surge_multiplier"
    )

    if prev:
        try:
            final = (0.65 * float(prev)) + (0.35 * final)
        except:
            pass

    final = max(1.0, min(final, 4.0))

    return (
        round(rule, 2),
        round(ml, 2),
        round(final, 2)
    )


def run():
    print("[INFO] Surge engine started")

    while True:
        try:
            drivers = group_by_zone(
                fetch_entities("driver")
            )

            riders = group_by_zone(
                fetch_entities("rider")
            )

            zones = set(drivers.keys()) | set(riders.keys())

            for zone in zones:
                d = drivers.get(zone, 0)
                r = riders.get(zone, 0)

                rule, ml, surge = calculate(d, r, zone)

                redis_client.hset(
                    f"surge:{zone}",
                    mapping={
                        "drivers": d,
                        "riders": r,
                        "rule_surge": rule,
                        "ml_surge": ml,
                        "surge_multiplier": surge,
                        "timestamp": time.time()
                    }
                )

                redis_client.expire(
                    f"surge:{zone}",
                    90
                )

            time.sleep(SURGE_INTERVAL)

        except Exception as e:
            print("Surge engine error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()