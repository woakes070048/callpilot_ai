import frappe
import requests
import json

@frappe.whitelist()
def initiate_call(lead_name):
    settings = frappe.get_single("CallPilot Settings")
    if not settings.vapi_api_key:
        frappe.throw("Please configure Vapi API Key in CallPilot Settings")
    
    lead = frappe.get_doc("Lead", lead_name)
    if not lead.mobile_no and not lead.phone:
        frappe.throw("Lead does not have a valid phone number")
        
    phone_number = lead.mobile_no or lead.phone
    
    url = 'https://api.vapi.ai/call/phone'
    headers = {
        'Authorization': f'Bearer {settings.vapi_api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "phoneNumber": {
            "twilioPhoneNumber": settings.twilio_phone_number,
            "number": phone_number
        },
        "customer": {
            "name": lead.lead_name,
            "number": phone_number
        },
        "assistant": {
            "firstMessage": f"Hi {lead.lead_name}, this is Sarah from Nexgen ERP Technologies. How are you doing today?",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional ERPNext consultant calling to qualify a lead. Ask them about their current software and schedule a 30 min demo."
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        frappe.msgprint(f"Call initiated successfully to {lead.lead_name}")
        return response.json()
    else:
        frappe.throw(f"Failed to initiate call: {response.text}")

