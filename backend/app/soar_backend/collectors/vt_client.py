import requests
from core.config import settings

def lookup_ip(ip):
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": settings.VT_API_KEY}
    return requests.get(url, headers=headers).json()
