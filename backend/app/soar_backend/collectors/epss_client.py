import requests

def lookup_epss(cve_id):
    # EPSS API is public
    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"errors": [f"EPSS API error: {response.status_code}"]}
    except requests.exceptions.RequestException as e:
        return {"errors": [str(e)]}