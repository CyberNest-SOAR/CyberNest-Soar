import requests, json
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings()

auth = HTTPBasicAuth('admin', 'SecretPassword')
url = 'https://localhost:9200'
headers = {'Content-Type': 'application/json'}

def search_rule(rule_id):
    body = {
        'size': 1,
        'query': {'match': {'rule.id': rule_id}}
    }
    r = requests.post(f'{url}/wazuh-alerts-*/_search', auth=auth, headers=headers, json=body, verify=False)
    data = r.json()
    total = data.get('hits', {}).get('total', {}).get('value', 0)
    print(f'Rule {rule_id}: {total} alerts')

print("--- Checking specific Zeek Rule IDs in OpenSearch ---")
for rid in ['100010', '100011', '100012', '100013', '100014', '100015']:
    search_rule(rid)

print("\n--- Checking for ANY alerts from zeek-agent ---")
body_agent = {
    'size': 5,
    'sort': [{'timestamp': {'order': 'desc'}}],
    'query': {'match': {'agent.name': 'zeek-agent'}}
}
r_agent = requests.post(f'{url}/wazuh-alerts-*/_search', auth=auth, headers=headers, json=body_agent, verify=False)
data_agent = r_agent.json()
total_agent = data_agent.get('hits', {}).get('total', {}).get('value', 0)
print(f'Total alerts for zeek-agent: {total_agent}')
for hit in data_agent.get('hits', {}).get('hits', []):
    src = hit['_source']
    print(f"  {src.get('timestamp')} | Rule {src.get('rule',{}).get('id')} | {src.get('rule',{}).get('description')[:50]}")
