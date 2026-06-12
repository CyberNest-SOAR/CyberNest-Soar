import json
import requests
from app.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def lookup_abuseip(ip):
    key = cache_key("abuseipdb:ip", ip)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    headers = {"Accept": "application/json", "Key": settings.ABUSE_KEY}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        result = response.json()
    except requests.exceptions.RequestException as e:
        result = {"errors": [str(e)]}

    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=300)
    except Exception:
        pass

    return result