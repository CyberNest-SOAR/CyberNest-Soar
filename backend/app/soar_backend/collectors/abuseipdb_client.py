import requests
from core.config import settings

def lookup_abuseip(ip):
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    headers = {"Accept": "application/json", "Key": settings.ABUSE_KEY}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"errors": [str(e)]}