import frappe
from frappe.model.document import Document

class LeadFinderCampaign(Document):
    def on_update(self):
        if self.status == "Draft":
            from callpilot_ai.api.scraper import trigger_scrape
            frappe.db.set_value("Lead Finder Campaign", self.name, "status", "Pending")
            trigger_scrape(self.name)
