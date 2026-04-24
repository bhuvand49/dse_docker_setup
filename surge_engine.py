import time
import random

from simulator.redis_client import redis_client
from ml.predictor import predict_surge, rule_based_surge

SURGE_INTERVAL = 2.0


def fetch_entities(prefix):
    rows = []
    for key in redis_client.scan_iter(f"{prefix}:*"):
        item = redis_client.hgetall(key)
        if item:
            rows.append(item)
    return rows


def group_by_zone(rows):
    result = {}
    for row in rows:
        zone = row.get("zone")
        if zone:
            result[zone] = result.get(zone, 0) + 1
    return result


def calculate(drivers, riders, zone):
    rule = rule_based_surge(drivers, riders)
    ml = predict_surge(drivers, riders, zone)

    # balanced blend
    final = (0.55 * rule) + (0.45 * ml)

    # stronger demand pressure
    if riders > drivers:
        gap = riders - drivers
        final += min(gap * 0.045, 1.7)

    # richer fluctuations
    final += random.uniform(-0.08, 0.15)

    # smooth previous state
    prev = redis_client.hget(f"surge:{zone}", "surge_multiplier")
    if prev:
        try:
            final = (0.60 * float(prev)) + (0.40 * final)
        except:
            pass

    final = max(1.0, min(final, 4.0))
    return round(rule, 2), round(ml, 2), round(final, 2)


def run():
    print("[INFO] Premium surge engine started")

    while True:
        try:
            drivers = group_by_zone(fetch_entities("driver"))
            riders = group_by_zone(fetch_entities("rider"))

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
                redis_client.expire(f"surge:{zone}", 90)

            time.sleep(SURGE_INTERVAL)

        except Exception as e:
            print("Premium surge engine error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()