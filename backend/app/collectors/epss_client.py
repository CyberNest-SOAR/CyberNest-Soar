import json
import requests

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def lookup_epss(cve_id):
    key = cache_key("epss:cve", cve_id)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            result = response.json()
        else:
            result = {"errors": [f"EPSS API error: {response.status_code}"]}
    except requests.exceptions.RequestException as e:
        result = {"errors": [str(e)]}

    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=300)
    except Exception:
        pass

    return result