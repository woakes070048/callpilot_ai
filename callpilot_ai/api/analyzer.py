import frappe

def run_analyzer(campaign_name):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    settings = frappe.get_single("Lead Finder Settings")
    
    if settings.llm_provider == "Google Gemini":
        pass
    elif settings.llm_provider == "OpenAI":
        pass
        
    frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Completed")
    frappe.db.commit()
