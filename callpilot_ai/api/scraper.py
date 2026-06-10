import frappe

@frappe.whitelist()
def trigger_scrape(campaign_name):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    frappe.enqueue(
        "callpilot_ai.api.scraper.run_scraper",
        queue="long",
        timeout=3600,
        campaign_name=campaign_name
    )
    return "Scraping Job Queued"

def run_scraper(campaign_name):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Scraping")
    frappe.db.commit()
    
    settings = frappe.get_single("Lead Finder Settings")
    
    if settings.scraper_engine == "Apify":
        pass
    else:
        pass
        
    frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Analyzing")
    frappe.db.commit()
    
    from callpilot_ai.api.analyzer import run_analyzer
    run_analyzer(campaign_name)
