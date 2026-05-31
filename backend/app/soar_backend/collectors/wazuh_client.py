import requests
from core.config import settings

def get_wazuh_token():
    url = f"{settings.WAZUH_URL}/security/user/authenticate"
    auth = (settings.WAZUH_USER, settings.WAZUH_PASS)
    response = requests.get(url, auth=auth, verify=False)
    return response.json().get("data", {}).get("token")

def get_wazuh_agent(agent_id):
    token = get_wazuh_token()
    url = f"{settings.WAZUH_URL}/agents?agents_list={agent_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers, verify=False).json()