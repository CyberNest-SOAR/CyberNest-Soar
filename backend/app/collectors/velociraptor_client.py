import json
import requests
from app.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def get_velociraptor_client(client_id):
    key = cache_key("velociraptor:client", client_id)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    url = f"{settings.VELOCIRAPTOR_URL}/api/v1/clients/{client_id}"
    resp = requests.get(url, timeout=5)
    try:
        result = resp.json()
    except Exception:
        result = {"_http_status": resp.status_code, "_text": resp.text}

    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=300)
    except Exception:
        pass

    return result