import json
import requests
from soar_backend.core.config import settings

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes


def get_wazuh_token():
    key = cache_key("wazuh:token")
    cached = get_bytes(key)
    if cached is not None:
        try:
            return cached.decode("utf-8")
        except Exception:
            pass

    url = f"{settings.WAZUH_URL}/security/user/authenticate"
    auth = (settings.WAZUH_USER, settings.WAZUH_PASS)
    response = requests.get(url, auth=auth, verify=False, timeout=5)
    token = response.json().get("data", {}).get("token")
    try:
        if token:
            set_bytes(key, token.encode("utf-8"), ttl=300)
    except Exception:
        pass
    return token


def get_wazuh_agent(agent_id):
    key = cache_key("wazuh:agent", agent_id)
    cached = get_bytes(key)
    if cached is not None:
        try:
            return json.loads(cached.decode("utf-8"))
        except Exception:
            pass

    token = get_wazuh_token()
    url = f"{settings.WAZUH_URL}/agents?agents_list={agent_id}"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers, verify=False, timeout=5).json()
    try:
        set_bytes(key, json.dumps(result, default=str).encode("utf-8"), ttl=300)
    except Exception:
        pass
    return result