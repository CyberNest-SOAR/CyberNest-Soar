from fastapi import FastAPI
 
from gmail_api import init_gmail_service, get_email_messages, get_email_message_details

app = FastAPI()

@app.get("/get_email_data")
def get_email_data(max_results:int=5):
    
    client_file = "client_secret.json"
    service = init_gmail_service(client_file)

    messages = get_email_messages(service, max_results=max_results)

    data = []

    for msg in messages:
        details = get_email_message_details(service, msg["id"])
        if details:
            data.append(details)

    return data