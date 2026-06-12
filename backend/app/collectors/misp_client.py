import json
from pymisp import ExpandedPyMISP
from app.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def lookup_misp(indicator):
    key = cache_key("misp:indicator", indicator)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    misp = ExpandedPyMISP(settings.MISP_URL, settings.MISP_KEY, ssl=False)
    result = misp.search(controller='attributes', value=indicator)

    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=300)
    except Exception:
        pass

    return result