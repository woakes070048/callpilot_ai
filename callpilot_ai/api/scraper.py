import frappe
import requests
import time

@frappe.whitelist()
def trigger_scrape(campaign_name):
    frappe.enqueue(
        "callpilot_ai.api.scraper.run_scraper",
        queue="default",
        timeout=3600,
        campaign_name=campaign_name
    )
    return "Scraping Job Queued"

def run_scraper(campaign_name):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Scraping")
    frappe.db.commit()
    
    settings = frappe.get_single("Lead Finder Settings")
    scraped_leads = []
    
    try:
        if settings.scraper_engine == "Apify":
            scraped_leads = run_apify_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
        else:
            scraped_leads = run_builtin_scraper(campaign.search_query, campaign.target_quantity)
            
        frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Analyzing")
        frappe.db.commit()
        
        from callpilot_ai.api.analyzer import run_analyzer
        run_analyzer(campaign_name, scraped_leads)
        
    except Exception as e:
        frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Failed")
        campaign.add_comment("Comment", text=f"**Error during scraping:** {str(e)}")
        frappe.db.commit()
        frappe.log_error(title="Scraper Error", message=str(e))

def run_apify_scraper(query, limit, api_key):
    if not api_key:
        raise Exception("Apify API Key is missing in Settings. Please add it or switch to Built-in Scraper.")
        
    url = f"https://api.apify.com/v2/acts/compass~google-maps-scraper/runs?token={api_key}"
    payload = {"searchStringsArray": [query], "maxCrawledPlacesPerSearch": limit, "language": "en"}
    run_res = requests.post(url, json=payload).json()
    
    if "error" in run_res:
        raise Exception(f"Apify Error: {run_res['error']['message']}")
        
    run_id = run_res.get("data", {}).get("id")
    dataset_id = run_res.get("data", {}).get("defaultDatasetId")
    
    while True:
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_key}"
        status_res = requests.get(status_url).json()
        status = status_res.get("data", {}).get("status")
        if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
            break
        time.sleep(10)
        
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_key}"
    items = requests.get(dataset_url).json()
    
    leads = []
    for item in items:
        if item.get("phone") or item.get("phoneUnformatted"):
            leads.append({
                "company_name": item.get("title") or "Unknown",
                "phone": item.get("phoneUnformatted") or item.get("phone"),
                "website": item.get("website")
            })
    return leads

def run_builtin_scraper(query, limit):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "addressdetails": 1, "extratags": 1, "limit": limit}
    headers = {"User-Agent": "CallPilotAI/1.0"}
    res = requests.get(url, params=params, headers=headers)
    
    if res.status_code != 200:
        raise Exception("Built-in Scraper Error: Map API rejected the request.")
        
    res_data = res.json()
    if not isinstance(res_data, list):
        raise Exception("Built-in Scraper Error: Unexpected response format from Map API.")
    
    leads = []
    for item in res_data:
        extratags = item.get("extratags", {})
        phone = extratags.get("phone") or extratags.get("contact:phone")
        website = extratags.get("website") or extratags.get("contact:website")
        
        if phone:
            leads.append({
                "company_name": item.get("name") or "Unknown Business",
                "phone": phone,
                "website": website
            })
    return leads
