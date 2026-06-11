import frappe
import requests

def analyze_call_transcript(lead_name, transcript):
    if not transcript or len(transcript) < 10:
        return
        
    settings = frappe.get_single("Lead Finder Settings")
    if settings.llm_provider != "Google Gemini" or not settings.llm_api_key:
        return
        
    prompt = f"Read the following phone call transcript between an AI sales agent and a prospect. Determine if the prospect is interested or not. Reply in exactly two lines. Line 1: 'Status: Interested' or 'Status: Not Interested'. Line 2: A one-sentence summary of the call. Transcript: {transcript}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.llm_api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        answer = res["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        lines = answer.split("\n")
        status_line = lines[0].upper()
        
        status = "Interested" if "INTERESTED" in status_line and "NOT" not in status_line else "Not Interested"
        
        frappe.db.set_value("Lead", lead_name, "status", status)
        
        lead = frappe.get_doc("Lead", lead_name)
        lead.add_comment("Comment", text=f"**AI Call Analysis:**\n{answer}")
        
    except Exception as e:
        frappe.log_error(title="Post-Call AI Error", message=str(e))
