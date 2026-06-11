import frappe
import requests
import json

@frappe.whitelist()
def trigger_bulk_calls(lead_names):
    if isinstance(lead_names, str):
        lead_names = json.loads(lead_names)
        
    if len(lead_names) <= 5:
        process_bulk_calls(lead_names)
    else:
        frappe.enqueue("callpilot_ai.api.bolna.process_bulk_calls", queue="short", timeout=3600, lead_names=lead_names)

def process_bulk_calls(lead_names):
    settings = frappe.get_single("Lead Finder Settings")
    
    for name in lead_names:
        lead = frappe.get_doc("Lead", name)
        
        if not settings.bolna_api_key or not settings.bolna_agent_id:
            lead.add_comment("Comment", text="**CallPilot AI Error:** Bolna API Key or Agent ID is missing in your Settings!")
            frappe.db.commit()
            continue

        headers = {
            "Authorization": f"Bearer {settings.bolna_api_key}",
            "Content-Type": "application/json"
        }

        phone = lead.mobile_no or lead.phone
        
        if not phone:
            lead.add_comment("Comment", text="**CallPilot AI Error:** Attempted to call, but no phone number exists.")
            frappe.db.commit()
            continue
            
        payload = {
            "agent_id": settings.bolna_agent_id,
            "recipient_phone_number": phone
        }
        
        try:
            res = requests.post("https://api.bolna.dev/call", json=payload, headers=headers)
            
            if res.status_code == 200:
                lead.add_comment("Comment", text=f"**CallPilot AI Voice Call Initiated!** Dialing {phone}...")
            else:
                lead.add_comment("Comment", text=f"**CallPilot AI Voice Error:** {res.text}")
                
            frappe.db.commit()
            
        except Exception as e:
            lead.add_comment("Comment", text=f"**CallPilot AI Server Error:** {str(e)}")
            frappe.db.commit()
            frappe.log_error(title=f"Bolna Call Failed for {name}", message=str(e))
