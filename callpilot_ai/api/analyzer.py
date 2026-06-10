import frappe
import requests
import json

def run_analyzer(campaign_name, scraped_leads):
    campaign = frappe.get_doc("Lead Finder Campaign", campaign_name)
    settings = frappe.get_single("Lead Finder Settings")
    prompt = campaign.qualification_prompt
    
    try:
        for lead_data in scraped_leads:
            company_name = lead_data.get("company_name")
            phone = lead_data.get("phone")
            website = lead_data.get("website")
            
            # If no prompt, just create the lead directly
            if not prompt:
                create_erpnext_lead(company_name, phone, website, campaign_name)
                continue
                
            # If prompt exists, analyze using AI
            is_qualified = True
            
            if settings.llm_provider == "Google Gemini" and settings.llm_api_key:
                is_qualified = analyze_with_gemini(company_name, website, prompt, settings.llm_api_key)
            elif settings.llm_provider == "OpenAI" and settings.llm_api_key:
                is_qualified = analyze_with_openai(company_name, website, prompt, settings.llm_api_key)
                
            if is_qualified:
                create_erpnext_lead(company_name, phone, website, campaign_name)
                
        frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Completed")
        frappe.db.commit()
        
    except Exception as e:
        frappe.db.set_value("Lead Finder Campaign", campaign_name, "status", "Failed")
        frappe.db.commit()
        frappe.log_error(title="Analyzer Error", message=str(e))

def analyze_with_gemini(company_name, website, prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    full_prompt = f"Analyze this company: {company_name}. Website: {website}. Criteria: {prompt}. Reply with exactly one word: YES if it meets criteria, or NO if it does not."
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    res = requests.post(url, headers=headers, json=payload).json()
    try:
        answer = res["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
        return "YES" in answer
    except:
        return True # Default to accept if AI fails to format

def analyze_with_openai(company_name, website, prompt, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    full_prompt = f"Analyze this company: {company_name}. Website: {website}. Criteria: {prompt}. Reply with exactly one word: YES if it meets criteria, or NO if it does not."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": full_prompt}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    res = requests.post(url, headers=headers, json=payload).json()
    try:
        answer = res["choices"][0]["message"]["content"].strip().upper()
        return "YES" in answer
    except:
        return True

def create_erpnext_lead(company_name, phone, website, campaign_name):
    # Check if lead exists
    exists = frappe.db.exists("Lead", {"mobile_no": phone}) or frappe.db.exists("Lead", {"phone": phone})
    if not exists:
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": company_name,
            "company_name": company_name,
            "mobile_no": phone,
            "website": website,
            "source": "Campaign",
            "campaign_name": campaign_name
        })
        lead.insert(ignore_permissions=True)
