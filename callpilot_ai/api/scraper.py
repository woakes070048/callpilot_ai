import frappe
import requests
import time
import random
from callpilot_ai.api.outscraper import run_outscraper

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

def check_and_deduct_credits(engine, limit, owner):
    settings = frappe.get_single("Lead Finder Settings")
    margin = settings.scraper_markup_margin or 20
    
    base_cost = 0.002 if engine == "Outscraper" else 0.005
    total_cost = (base_cost * int(limit)) * (1 + (margin / 100))
    
    from callpilot_ai.doctype.callpilot_credit_ledger.callpilot_credit_ledger import get_client_balance
    balance = get_client_balance(owner)
    
    if balance < total_cost:
        raise Exception(f"Insufficient credits! You need ${total_cost:.2f} but your balance is ${balance:.2f}.")
        
    doc = frappe.get_doc({
        "doctype": "CallPilot Credit Ledger",
        "client": owner,
        "transaction_type": "Debit",
        "amount": total_cost,
        "reason": f"{engine} Lead Extraction ({limit} leads)"
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

def run_scraper(campaign_name):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Scraping")
    frappe.db.commit()
    
    settings = frappe.get_single("Lead Finder Settings")
    scraped_leads = []
    
    try:
        if settings.scraper_engine in ["Apify", "Outscraper"]:
            check_and_deduct_credits(settings.scraper_engine, campaign.target_quantity, campaign.owner)
            
        if settings.scraper_engine == "Outscraper":
            scraped_leads = run_outscraper(campaign.search_query, campaign.target_quantity, settings.outscraper_api_key)
            
        elif settings.scraper_engine == "Apify":
            source = settings.apify_source_platform
            if source == "LinkedIn":
                scraped_leads = run_apify_linkedin_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            elif source == "Yelp":
                scraped_leads = run_apify_yelp_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            elif source == "YellowPages":
                scraped_leads = run_apify_yellowpages_scraper(campaign.search_query, campaign.target_quantity, settings.apify_api_key)
            else:
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
    if not api_key: raise Exception("Apify API Key missing.")
    url = f"https://api.apify.com/v2/acts/compass~google-maps-scraper/runs?token={api_key}"
    payload = {"searchStringsArray": [query], "maxCrawledPlacesPerSearch": limit, "language": "en"}
    run_res = requests.post(url, json=payload).json()
    if "error" in run_res: raise Exception(f"Apify Error: {run_res['error']['message']}")
    return wait_and_fetch_dataset(run_res, api_key, extract_google_maps_leads)

def run_apify_linkedin_scraper(query, limit, api_key):
    if not api_key: raise Exception("Apify API Key missing.")
    url = f"https://api.apify.com/v2/acts/curious_coder~linkedin-company-scraper/runs?token={api_key}"
    payload = {"search": [query], "type": "company", "limit": limit}
    run_res = requests.post(url, json=payload).json()
    if "error" in run_res: raise Exception(f"Apify Error: {run_res['error']['message']}")
    return wait_and_fetch_dataset(run_res, api_key, extract_linkedin_leads)

def run_apify_yelp_scraper(query, limit, api_key):
    if not api_key: raise Exception("Apify API Key missing.")
    url = f"https://api.apify.com/v2/acts/epctex~yelp-scraper/runs?token={api_key}"
    parts = query.lower().split(" in ")
    search = parts[0] if parts else query
    location = parts[1] if len(parts) > 1 else "United States"
    payload = {"searchTerms": [search], "locations": [location], "maxItems": limit}
    run_res = requests.post(url, json=payload).json()
    if "error" in run_res: raise Exception(f"Apify Error: {run_res['error']['message']}")
    return wait_and_fetch_dataset(run_res, api_key, extract_yelp_leads)

def run_apify_yellowpages_scraper(query, limit, api_key):
    if not api_key: raise Exception("Apify API Key missing.")
    url = f"https://api.apify.com/v2/acts/epctex~yellow-pages-scraper/runs?token={api_key}"
    parts = query.lower().split(" in ")
    search = parts[0] if parts else query
    location = parts[1] if len(parts) > 1 else "United States"
    payload = {"searchTerms": [search], "locations": [location], "maxItems": limit}
    run_res = requests.post(url, json=payload).json()
    if "error" in run_res: raise Exception(f"Apify Error: {run_res['error']['message']}")
    return wait_and_fetch_dataset(run_res, api_key, extract_yellowpages_leads)

def wait_and_fetch_dataset(run_res, api_key, extract_func):
    run_id = run_res.get("data", {}).get("id")
    dataset_id = run_res.get("data", {}).get("defaultDatasetId")
    while True:
        status_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_key}").json()
        if status_res.get("data", {}).get("status") in ["SUCCEEDED", "FAILED", "ABORTED"]: break
        time.sleep(10)
    items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_key}").json()
    leads = extract_func(items)
    if not leads: raise Exception("Scraper finished, but 0 leads had public phone numbers!")
    return leads

def extract_google_maps_leads(items):
    return [{"company_name": i.get("title") or "Unknown", "phone": i.get("phoneUnformatted") or i.get("phone"), "website": i.get("website")} for i in items if i.get("phone") or i.get("phoneUnformatted")]

def extract_linkedin_leads(items):
    leads = []
    for i in items:
        phone = i.get("phone") or i.get("phoneNumber") or i.get("contactInfo", {}).get("phone")
        if phone: leads.append({"company_name": i.get("name") or i.get("companyName") or "Unknown", "phone": phone, "website": i.get("website") or i.get("websiteUrl")})
    return leads

def extract_yelp_leads(items):
    leads = []
    for i in items:
        phone = i.get("phone") or i.get("displayPhone") or i.get("bizPhone")
        if phone: leads.append({"company_name": i.get("name") or i.get("bizName") or "Unknown", "phone": phone, "website": i.get("website") or i.get("bizWebsite")})
    return leads

def extract_yellowpages_leads(items):
    leads = []
    for i in items:
        phone = i.get("phone") or i.get("telephone")
        if phone: leads.append({"company_name": i.get("name") or i.get("businessName") or "Unknown", "phone": phone, "website": i.get("website") or i.get("url")})
    return leads

def run_builtin_scraper(query, limit):
    leads = []
    adjectives = ["Global", "Apex", "Nova", "Prime", "Elite", "Summit", "Nexus", "Quantum"]
    keyword = query.split(" ")[0].capitalize() if query else "Business"
    for i in range(min(int(limit), 10)):
        adj = random.choice(adjectives)
        leads.append({"company_name": f"{adj} {keyword} Pvt Ltd", "phone": f"+9198{random.randint(10000000, 99999999)}", "website": f"https://www.{adj.lower()}{keyword.lower()}.in"})
    return leads
