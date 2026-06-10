import frappe
import requests
from bs4 import BeautifulSoup
import json
from callpilot_ai.api.analyzer import get_llm_decision

@frappe.whitelist()
def trigger_bulk_analysis(lead_names, ai_prompt):
    if isinstance(lead_names, str):
        lead_names = json.loads(lead_names)
    
    frappe.enqueue("callpilot_ai.api.bulk_analyzer.process_bulk_analysis", queue="long", timeout=7200, lead_names=lead_names, ai_prompt=ai_prompt)

def process_bulk_analysis(lead_names, ai_prompt):
    settings = frappe.get_single("Lead Finder Settings")
    
    if not settings.llm_provider or not settings.llm_api_key:
        frappe.log_error(title="Bulk AI Error", message="LLM Provider or API Key is missing in settings.")
        return

    for name in lead_names:
        lead = frappe.get_doc("Lead", name)
        
        if not lead.website:
            lead.status = "Do Not Contact"
            lead.add_comment("Comment", text="**AI Disqualified:** No website URL was provided for analysis.")
            lead.save(ignore_permissions=True)
            continue
            
        try:
            res = requests.get(lead.website, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)[:3000] 
            
            prompt = f"Website text: {text_content}\n\nQuestion: {ai_prompt}\n\nReply with exactly two words: 'YES' or 'NO', followed by a hyphen and a one-sentence explanation."
            
            answer = get_llm_decision(prompt, settings)
            
            if answer.strip().upper().startswith("YES"):
                lead.status = "Qualified"
                lead.add_comment("Comment", text=f"**AI Qualified:** {answer}")
            else:
                lead.status = "Do Not Contact"
                lead.add_comment("Comment", text=f"**AI Disqualified:** {answer}")
                
            lead.save(ignore_permissions=True)
            
        except Exception as e:
            lead.status = "Do Not Contact"
            lead.add_comment("Comment", text=f"**AI Error:** Failed to scrape website ({str(e)}).")
            lead.save(ignore_permissions=True)
