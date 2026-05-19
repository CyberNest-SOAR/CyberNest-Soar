import requests
import json
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== Wazuh API =====
class WazuhAPI:
    def __init__(self, url='https://localhost:55000', username='wazuh-wui', password='MyS3cr37P450r.*-'):
        self.url = url
        self.username = username
        self.password = password
        self.headers = {'Content-Type': 'application/json'}
        self.token = None
        self._get_token()

    def _get_token(self):
        token_url = f"{self.url}/security/user/authenticate"
        response = requests.post(token_url, auth=HTTPBasicAuth(self.username, self.password), headers=self.headers, verify=False)
        if response.status_code == 200:
            self.token = response.json()['data']['token']
            self.headers['Authorization'] = f'Bearer {self.token}'
            print("Token fetched successfully!")
        else:
            raise ValueError(f"Token error: {response.status_code} - {response.text}")

    def get_agents(self):
        agents_url = f"{self.url}/agents?pretty=true"
        response = requests.get(agents_url, headers=self.headers, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Agents error: {response.status_code} - {response.text}")

# ===== OpenSearch API =====
class OpenSearchAPI:
    def __init__(self, url='https://localhost:9200', username='admin', password='SecretPassword'):
        self.url = url
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {'Content-Type': 'application/json'}

    def get_last_10_logs_full(self):
        """جيب آخر 10 logs مع كل التفاصيل (Full JSON لكل event)"""
        search_url = f"{self.url}/wazuh-alerts-*/_search"
        body = {
            "size": 10,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"match_all": {}}
        }
        response = requests.post(search_url, auth=self.auth, headers=self.headers, json=body, verify=False)
        if response.status_code == 200:
            data = response.json()
            total = data['hits']['total']['value']
            print(f"\nTotal alerts in index: {total}")
            print("=" * 100)
            print(f"Last 10 Logs (Full Details) - أحدث الأول")
            print("=" * 100)
            
            for i, hit in enumerate(data['hits']['hits'], 1):
                source = hit['_source']
                print(f"\nLog {i} / 10")
                print("-" * 80)
                # طباعة كل التفاصيل بطريقة مرتبة وجميلة
                print(json.dumps(source, indent=4, ensure_ascii=False))
                print("-" * 80)
            return data
        else:
            raise ValueError(f"Error: {response.status_code} - {response.text}")

# ===== Main =====
if __name__ == "__main__":
    # 1. Wazuh Agents
    wazuh = WazuhAPI()
    print("=== Wazuh Agents (Full Details) ===")
    agents = wazuh.get_agents()
    print(json.dumps(agents, indent=4, ensure_ascii=False))

    # 2. Last 10 Logs with FULL details
    opensearch = OpenSearchAPI()
    print("\n=== Last 10 Wazuh Logs/Alerts (FULL DETAILS) ===")
    logs = opensearch.get_last_10_logs_full()

    print("\nDone! Fetched agents + last 10 logs with complete details.")
