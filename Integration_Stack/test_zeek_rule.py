"""
Test what rule fires for a Zeek log event using Wazuh API logtest endpoint
"""
import requests, json
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings()

# Get Wazuh API token
api_url = 'https://localhost:55000'
auth = HTTPBasicAuth('wazuh-wui', 'MyS3cr37P450r.*-')
headers = {'Content-Type': 'application/json'}

r = requests.post(f'{api_url}/security/user/authenticate', auth=auth, headers=headers, verify=False)
token = r.json()['data']['token']
headers['Authorization'] = f'Bearer {token}'
print(f'[+] Token obtained')

# Test a Zeek conn.log line via logtest API
zeek_log = '{"ts":1778871999.0,"uid":"TEST_ZEEK_001","id.orig_h":"1.2.3.4","id.orig_p":1234,"id.resp_h":"5.6.7.8","id.resp_p":80,"proto":"tcp","service":"http","conn_state":"SF","orig_bytes":1000,"resp_bytes":500}'

body = {
    'log_format': 'json',
    'location': '/var/log/zeek/conn.log',
    'event': zeek_log
}
r2 = requests.put(f'{api_url}/logtest', headers=headers, json=body, verify=False)
print('\n=== Logtest result for Zeek conn.log ===')
result = r2.json()
print(json.dumps(result, indent=2))
