import frappe
import requests
import time
import random

@frappe.whitelist()
def trigger_scrape(campaign_name):
    frappe.enqueue(
        "callpilot_ai.api.scraper.run_scraper",
        queue="default",
        timeout=3600,
        enqueue_after_commit=True,
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
            source = settings.apify_source_platform
            
            if source == "LinkedIn":
                scraped_leads = run_apify_linkedin_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            elif source == "Yelp":
                scraped_leads = run_apify_yelp_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            elif source == "YellowPages":
                scraped_leads = run_apify_yellowpages_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            else:
                # Default to Google Maps
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
    # GOOGLE MAPS SCRAPER
    if not api_key:
        raise Exception("Apify API Key is missing in Settings.")
        
    url = f"https://api.apify.com/v2/acts/compass~google-maps-scraper/runs?token={api_key}"
    payload = {"searchStringsArray": [query], "maxCrawledPlacesPerSearch": limit, "language": "en"}
    run_res = requests.post(url, json=payload).json()
    
    if "error" in run_res:
        raise Exception(f"Apify Error: {run_res['error']['message']}")
        
    return wait_and_fetch_dataset(run_res, api_key, extract_google_maps_leads)


def run_apify_linkedin_scraper(query, limit, api_key):
    # LINKEDIN COMPANY SCRAPER
    if not api_key:
        raise Exception("Apify API Key is missing in Settings.")
        
    url = f"https://api.apify.com/v2/acts/curious_coder~linkedin-company-scraper/runs?token={api_key}"
    payload = {"search": [query], "type": "company", "limit": limit}
    run_res = requests.post(url, json=payload).json()
    
    if "error" in run_res:
        raise Exception(f"Apify Error: {run_res['error']['message']}")
        
    return wait_and_fetch_dataset(run_res, api_key, extract_linkedin_leads)


def run_apify_yelp_scraper(query, limit, api_key):
    # YELP SCRAPER
    if not api_key:
        raise Exception("Apify API Key is missing in Settings.")
        
    # We use a popular yelp scraper actor. Note: The exact actor ID can be modified here if needed.
    url = f"https://api.apify.com/v2/acts/epctex~yelp-scraper/runs?token={api_key}"
    
    # Split query into search term and location if possible (e.g. "Plumbers in Austin" -> search: Plumbers, location: Austin)
    parts = query.lower().split(" in ")
    search = parts[0] if parts else query
    location = parts[1] if len(parts) > 1 else "United States"
    
    payload = {"searchTerms": [search], "locations": [location], "maxItems": limit}
    run_res = requests.post(url, json=payload).json()
    
    if "error" in run_res:
        raise Exception(f"Apify Error: {run_res['error']['message']}")
        
    return wait_and_fetch_dataset(run_res, api_key, extract_yelp_leads)


def run_apify_yellowpages_scraper(query, limit, api_key):
    # YELLOWPAGES SCRAPER
    if not api_key:
        raise Exception("Apify API Key is missing in Settings.")
        
    url = f"https://api.apify.com/v2/acts/epctex~yellow-pages-scraper/runs?token={api_key}"
    
    parts = query.lower().split(" in ")
    search = parts[0] if parts else query
    location = parts[1] if len(parts) > 1 else "United States"
    
    payload = {"searchTerms": [search], "locations": [location], "maxItems": limit}
    run_res = requests.post(url, json=payload).json()
    
    if "error" in run_res:
        raise Exception(f"Apify Error: {run_res['error']['message']}")
        
    return wait_and_fetch_dataset(run_res, api_key, extract_yellowpages_leads)


# --- HELPER FUNCTIONS ---

def wait_and_fetch_dataset(run_res, api_key, extract_func):
    """Wait for the Apify Actor to finish and return the parsed leads."""
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
    
    leads = extract_func(items)
    if not leads:
        raise Exception("Scraper finished, but 0 leads had public phone numbers! (Strict Phone Rule applied)")
        
    return leads


def extract_google_maps_leads(items):
    leads = []
    for item in items:
        if item.get("phone") or item.get("phoneUnformatted"):
            leads.append({
                "company_name": item.get("title") or "Unknown",
                "phone": item.get("phoneUnformatted") or item.get("phone"),
                "website": item.get("website")
            })
    return leads


def extract_linkedin_leads(items):
    leads = []
    for item in items:
        phone = item.get("phone") or item.get("phoneNumber") or item.get("contactInfo", {}).get("phone")
        if not phone:
            continue # Strict Phone Rule
        leads.append({
            "company_name": item.get("name") or item.get("companyName") or "Unknown LinkedIn Company",
            "phone": phone,
            "website": item.get("website") or item.get("websiteUrl")
        })
    return leads


def extract_yelp_leads(items):
    leads = []
    for item in items:
        phone = item.get("phone") or item.get("displayPhone") or item.get("bizPhone")
        if not phone:
            continue # Strict Phone Rule
        leads.append({
            "company_name": item.get("name") or item.get("bizName") or "Unknown Yelp Business",
            "phone": phone,
            "website": item.get("website") or item.get("bizWebsite")
        })
    return leads


def extract_yellowpages_leads(items):
    leads = []
    for item in items:
        phone = item.get("phone") or item.get("telephone")
        if not phone:
            continue # Strict Phone Rule
        leads.append({
            "company_name": item.get("name") or item.get("businessName") or "Unknown YP Business",
            "phone": phone,
            "website": item.get("website") or item.get("url")
        })
    return leads


def run_builtin_scraper(query, limit):
    # Mock Data Generator for Free Testing
    leads = []
    adjectives = ["Global", "Apex", "Nova", "Prime", "Elite", "Summit", "Nexus", "Quantum"]
    keyword = query.split(" ")[0].capitalize() if query else "Business"
    
    for i in range(min(int(limit), 10)):
        adj = random.choice(adjectives)
        company_name = f"{adj} {keyword} Pvt Ltd"
        phone = f"+9198{random.randint(10000000, 99999999)}"
        website = f"https://www.{adj.lower()}{keyword.lower()}.in"
        
        leads.append({
            "company_name": company_name,
            "phone": phone,
            "website": website
        })
    return leads
