import frappe
from frappe.model.document import Document

class CallPilotCreditLedger(Document):
    pass

@frappe.whitelist()
def get_client_balance(client):
    credits = frappe.db.sql("SELECT SUM(amount) FROM 	abCallPilot Credit Ledger WHERE client=%s AND transaction_type='Credit'", client)
    debits = frappe.db.sql("SELECT SUM(amount) FROM 	abCallPilot Credit Ledger WHERE client=%s AND transaction_type='Debit'", client)
    
    total_credit = credits[0][0] if credits and credits[0][0] else 0
    total_debit = debits[0][0] if debits and debits[0][0] else 0
    
    return total_credit - total_debit
