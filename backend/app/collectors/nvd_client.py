import json
import requests
from app.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def lookup_cvss(cve_id):
    if not settings.NVD_API_KEY:
        return {"errors": ["NVD API Key not configured"]}

    key = cache_key("nvd:cve", cve_id)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    headers = {"Accept": "application/json", "apiKey": settings.NVD_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            result = response.json()
        elif response.status_code == 404:
            result = {"errors": ["CVE ID not found"]}
        elif response.status_code == 403:
            result = {"errors": ["NVD API key rate limit exceeded or invalid"]}
        else:
            result = {"errors": [f"NVD API error: {response.status_code}"]}
    except requests.exceptions.RequestException as e:
        result = {"errors": [str(e)]}

    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=3600)
    except Exception:
        pass

    return result