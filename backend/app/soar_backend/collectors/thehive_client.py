import requests
from core.config import settings

def create_case(title, severity):
    url = f"{settings.THEHIVE_URL}/api/v1/case"
    headers = {
        "Authorization": f"Bearer {settings.THEHIVE_API_KEY}"
    }

    data = {
        "title": title,
        "severity": severity
    }

    return requests.post(url, json=data, headers=headers).json()