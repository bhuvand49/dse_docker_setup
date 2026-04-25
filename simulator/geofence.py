import h3

# Keep SAME resolution across entire project
RESOLUTION = 7


def get_zone(lat: float, lon: float) -> str:
    """
    Convert latitude/longitude into H3 zone id.
    Must match api.py grid resolution.
    """
    return h3.latlng_to_cell(lat, lon, RESOLUTION)