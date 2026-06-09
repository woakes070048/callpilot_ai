import frappe
import json

@frappe.whitelist(allow_guest=True)
def vapi_webhook():
    try:
        data = frappe.request.get_data()
        payload = json.loads(data)
        
        if payload.get("message", {}).get("type") == "end-of-call-report":
            call_data = payload.get("message")
            customer_number = call_data.get("customer", {}).get("number")
            transcript = call_data.get("transcript")
            summary = call_data.get("summary")
            
            if not customer_number:
                return "No customer number found"
                
            leads = frappe.get_all("Lead", filters={"mobile_no": customer_number})
            if not leads:
                leads = frappe.get_all("Lead", filters={"phone": customer_number})
                
            if leads:
                lead_name = leads[0].name
                
                log = frappe.get_doc({
                    "doctype": "CallPilot Log",
                    "lead": lead_name,
                    "call_summary": summary,
                    "call_transcript": transcript,
                    "call_duration": call_data.get("duration", 0)
                })
                log.insert(ignore_permissions=True)
                
                frappe.db.set_value("Lead", lead_name, "status", "Contacted")
                frappe.db.commit()
                
        return "Success"
    except Exception as e:
        frappe.log_error(title="Vapi Webhook Error", message=frappe.get_traceback())
        return "Error"


