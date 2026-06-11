import frappe
import requests
from bs4 import BeautifulSoup
import json

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
            
            full_prompt = f"Website text: {text_content}\n\nQuestion: {ai_prompt}\n\nReply with exactly two words: 'YES' or 'NO', followed by a hyphen and a one-sentence explanation."
            
            answer = "NO - Could not parse"
            
            if settings.llm_provider == "Google Gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.llm_api_key}"
                payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                headers = {"Content-Type": "application/json"}
                res = requests.post(url, headers=headers, json=payload).json()
                answer = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                
            elif settings.llm_provider == "OpenAI":
                url = "https://api.openai.com/v1/chat/completions"
                payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": full_prompt}]}
                headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
                res = requests.post(url, headers=headers, json=payload).json()
                answer = res["choices"][0]["message"]["content"].strip()
            
            if answer.upper().startswith("YES"):
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
