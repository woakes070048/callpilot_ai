import frappe
import requests
import json

@frappe.whitelist()
def trigger_bulk_calls(lead_names):
    if isinstance(lead_names, str):
        lead_names = json.loads(lead_names)
        
    frappe.enqueue("callpilot_ai.api.bolna.process_bulk_calls", queue="default", timeout=3600, lead_names=lead_names)

def process_bulk_calls(lead_names):
    settings = frappe.get_single("Lead Finder Settings")
    if not settings.bolna_api_key or not settings.bolna_agent_id:
        frappe.log_error(title="Bolna Error", message="Bolna API Key or Agent ID is missing in settings.")
        return

    headers = {
        "Authorization": f"Bearer {settings.bolna_api_key}",
        "Content-Type": "application/json"
    }

    for name in lead_names:
        lead = frappe.get_doc("Lead", name)
        phone = lead.mobile_no or lead.phone
        
        if not phone:
            lead.add_comment("Comment", text="Bolna AI attempted to call, but no phone number exists.")
            continue
            
        payload = {
            "agent_id": settings.bolna_agent_id,
            "recipient_phone_number": phone
        }
        
        try:
            res = requests.post("https://api.bolna.dev/call", json=payload, headers=headers)
            
            if res.status_code == 200:
                lead.add_comment("Comment", text=f"**Bolna AI Outbound Call Initiated!** Dialing {phone}...")
            else:
                lead.add_comment("Comment", text=f"**Bolna API Error:** {res.text}")
                
        except Exception as e:
            frappe.log_error(title=f"Bolna Call Failed for {name}", message=str(e))
