import frappe
import requests
import json

@frappe.whitelist()
def trigger_bulk_calls(lead_names):
    if isinstance(lead_names, str):
        lead_names = json.loads(lead_names)
        
    if len(lead_names) == 1:
        return process_single_call(lead_names[0])
    else:
        frappe.enqueue("callpilot_ai.api.bolna.process_bulk_calls", queue="short", timeout=3600, lead_names=lead_names)
        return "queued"

def process_single_call(name):
    settings = frappe.get_single("Lead Finder Settings")
    lead = frappe.get_doc("Lead", name)
    
    if not settings.bolna_api_key or not settings.bolna_agent_id:
        return "<b>ERROR:</b> Bolna API Key or Agent ID is missing in Lead Finder Settings!"

    headers = {
        "Authorization": f"Bearer {settings.bolna_api_key}",
        "Content-Type": "application/json"
    }

    phone = lead.mobile_no or lead.phone
    if not phone:
        return "<b>ERROR:</b> This lead has no phone number."
        
    payload = {
        "agent_id": settings.bolna_agent_id,
        "recipient_phone_number": phone
    }
    
    try:
        res = requests.post("https://api.bolna.dev/call", json=payload, headers=headers)
        if res.status_code == 200:
            return f"<b>SUCCESS:</b> Bolna is dialing {phone} right now!"
        else:
            return f"<b>BOLNA API ERROR:</b><br>{res.text}"
            
    except Exception as e:
        return f"<b>SERVER ERROR:</b> {str(e)}"

def process_bulk_calls(lead_names):
    for name in lead_names:
        process_single_call(name)
