from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://mail.google.com/"]
CLIENT_SECRET_FILE = "client_secret/client_secret.json"
TOKEN_FILE = "token_files/token_gmail_v1.json"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

# Save token for Docker to use
import os
os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())
