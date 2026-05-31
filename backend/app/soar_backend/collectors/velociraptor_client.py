import requests
from core.config import settings

def get_velociraptor_client(client_id):
    url = f"{settings.VELOCIRAPTOR_URL}/api/v1/clients/{client_id}"
    return requests.get(url).json()