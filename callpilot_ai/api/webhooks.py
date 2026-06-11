import frappe
import requests
import json

@frappe.whitelist(allow_guest=True)
def bolna_call_completed():
    payload = frappe.request.get_data(as_text=True)
    if not payload:
        return "No payload"
        
    try:
        data = json.loads(payload)
    except:
        return "Invalid JSON"
        
    execution_id = data.get("execution_id") or data.get("id")
    if not execution_id:
        return "No execution_id"
        
    settings = frappe.get_single("Lead Finder Settings")
    if not settings.bolna_api_key:
        return "No Bolna API key"
        
    url = f"https://api.bolna.dev/execution/{execution_id}"
    headers = {"Authorization": f"Bearer {settings.bolna_api_key}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return f"Failed to fetch Bolna execution: {res.text}"
            
        exec_data = res.json()
    except Exception as e:
        frappe.log_error(title="Bolna Webhook Error", message=str(e))
        return "API Error"
        
    phone = exec_data.get("recipient_phone_number") or data.get("recipient_phone_number")
    transcript = exec_data.get("transcript", "No transcript available.")
    recording_url = exec_data.get("recording_url")
    
    if not phone:
        return "No phone number found"
        
    lead_name = frappe.db.get_value("Lead", {"mobile_no": phone}, "name")
    if not lead_name:
        lead_name = frappe.db.get_value("Lead", {"phone": phone}, "name")
        
    if not lead_name:
        return "Lead not found"
        
    lead = frappe.get_doc("Lead", lead_name)
    
    comment_text = f"**Bolna Call Completed**\n\n**Transcript:**\n{transcript}"
    if recording_url:
        comment_text += f"\n\n[Listen to Recording]({recording_url})"
        
    lead.add_comment("Comment", text=comment_text)
    
    try:
        from callpilot_ai.api.post_call_analyzer import analyze_call_transcript
        analyze_call_transcript(lead_name, transcript)
    except Exception as e:
        frappe.log_error("Analyzer Import Error", str(e))
    
    frappe.db.commit()
    return "Success"
