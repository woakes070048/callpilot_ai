import frappe

frappe.init(site="nexgenerp.frappe.cloud")
frappe.connect()

comments = frappe.get_all("Comment", filters={"reference_doctype": "Lead"}, fields=["reference_name", "content"], order_by="creation desc", limit=10)

for c in comments:
    if "**AI" in c.content:
        print(f"Lead: {c.reference_name} | Comment: {c.content}")
