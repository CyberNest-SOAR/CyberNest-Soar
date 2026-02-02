import os
import time
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings()

VELO_URL = os.getenv("VELO_URL", "https://localhost:8000")
VELO_USERNAME = os.getenv("VELO_USERNAME", "admin")
VELO_PASSWORD = os.getenv("VELO_PASSWORD", "admin")

ARKIME_URL = os.getenv("ARKIME_URL", "http://localhost:8005")
ARKIME_USER = os.getenv("ARKIME_USER", "admin")
ARKIME_PASS = os.getenv("ARKIME_PASS", "admin")


def make_session():
    """Create a requests session with retries."""
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def velo_login(session: requests.Session):
    """Login to Velociraptor and attach bearer token to the session."""
    r = session.post(
        f"{VELO_URL}/api/v1/login",
        json={"username": VELO_USERNAME, "password": VELO_PASSWORD},
        verify=False,
        timeout=10
    )
    r.raise_for_status()
    token = r.json().get("token")
    if not token:
        raise RuntimeError("Velociraptor login succeeded but token missing.")
    session.headers.update({"Authorization": f"Bearer {token}"})


def get_velo_clients(session: requests.Session):
    """Fetch Velociraptor clients list."""
    r = session.get(f"{VELO_URL}/api/v1/clients", verify=False, timeout=10)
    r.raise_for_status()
    return r.json()


def get_arkime_sessions(last_seconds=3600):
    """Fetch Arkime sessions in the last N seconds."""
    now = int(time.time())
    start = now - last_seconds
    r = requests.get(
        f"{ARKIME_URL}/api/sessions.json",
        params={"startTime": start, "endTime": now},
        auth=(ARKIME_USER, ARKIME_PASS),
        timeout=15
    )
    r.raise_for_status()
    return r.json()


def main():
    s = make_session()

    # Velociraptor
    velo_login(s)
    clients = get_velo_clients(s)
    print("Velociraptor Clients count:", len(clients.get("items", [])))

    # Arkime
    ark_sessions = get_arkime_sessions(3600)
    print("Arkime Sessions keys:", ark_sessions.keys())

if __name__ == "__main__":
    main()
