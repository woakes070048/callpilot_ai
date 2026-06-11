import frappe

@frappe.whitelist()
def get_dashboard_data():
    total_leads = frappe.db.count("Lead")
    interested = frappe.db.count("Lead", {"status": "Interested"})
    not_interested = frappe.db.count("Lead", {"status": "Not Interested"})
    
    # Calculate called
    called = interested + not_interested
    
    # Failed calls
    failed = frappe.db.count("Lead", {"status": "Do Not Contact"})
    
    return {
        "total_leads": total_leads,
        "interested": interested,
        "not_interested": not_interested,
        "called": called,
        "failed": failed
    }
