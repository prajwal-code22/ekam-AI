from math import asin, cos, radians, sin, sqrt

from jobs.models import Worker


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in kilometres."""
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def nearest_workers(trade, lat, lng, limit=3):
    """Nearest available workers for a trade. Falls back to any trade if none match."""
    available = list(Worker.objects.filter(available=True))
    pool = [w for w in available if w.trade == trade] or available
    ranked = sorted(pool, key=lambda w: haversine_km(lat, lng, w.lat, w.lng))
    return [(w, round(haversine_km(lat, lng, w.lat, w.lng), 1)) for w in ranked[:limit]]
