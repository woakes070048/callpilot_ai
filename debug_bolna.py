import frappe
frappe.init(site="nexgenerp.frappe.cloud")
frappe.connect()

print("--- RECENT LEAD COMMENTS ---")
comments = frappe.get_all("Comment", filters={"reference_doctype": "Lead"}, fields=["reference_name", "content"], order_by="creation desc", limit=5)
for c in comments:
    print(f"Lead: {c.reference_name} | {c.content}")

print("\n--- RECENT ERROR LOGS ---")
errors = frappe.get_all("Error Log", fields=["method", "error"], order_by="creation desc", limit=3)
for e in errors:
    print(f"Method: {e.method}")
    print(f"Error: {e.error}")
