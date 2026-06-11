import requests

def run_outscraper(query, limit, api_key):
    if not api_key:
        raise Exception("Outscraper API Key is missing in Settings.")
        
    url = f"https://api.app.outscraper.com/maps/search-v2"
    params = {
        "query": query,
        "limit": limit,
        "language": "en"
    }
    headers = {
        "X-API-KEY": api_key
    }
    
    res = requests.get(url, params=params, headers=headers)
    
    if res.status_code != 200:
        raise Exception(f"Outscraper API Error: {res.text}")
        
    data = res.json()
    if "data" not in data or not data["data"]:
        raise Exception("Outscraper returned no data for this query.")
        
    items = data["data"][0] # Outscraper returns a list of results inside the first element
    
    leads = []
    for item in items:
        phone = item.get("phone")
        if not phone:
            continue
            
        leads.append({
            "company_name": item.get("name") or "Unknown Outscraper Business",
            "phone": phone,
            "website": item.get("site") or item.get("website")
        })
        
    if not leads:
        raise Exception("Scraper finished, but 0 leads had public phone numbers!")
        
    return leads
