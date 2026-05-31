import requests
from core.config import settings

def lookup_cvss(cve_id):
    # Check if NVD API key is set
    if not settings.NVD_API_KEY:
        return {"errors": ["NVD API Key not configured"]}

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    
    headers = {
        "Accept": "application/json",
        "apiKey": settings.NVD_API_KEY  # Use 'apiKey' for NVD
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"errors": ["CVE ID not found"]}
        elif response.status_code == 403:
            return {"errors": ["NVD API key rate limit exceeded or invalid"]}
        else:
            return {"errors": [f"NVD API error: {response.status_code}"]}
            
    except requests.exceptions.RequestException as e:
        return {"errors": [str(e)]}