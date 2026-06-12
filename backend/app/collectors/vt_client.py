import json
import requests
from app.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def lookup_ip(ip):
    key = cache_key("vt:ip", ip)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": settings.VT_API_KEY}
    resp = requests.get(url, headers=headers, timeout=5)
    try:
        result = resp.json()
    except Exception:
        result = {"_http_status": resp.status_code, "_text": resp.text}

    try:
        set_bytes(key, resp.content, ttl=300)
    except Exception:
        pass

    return result
