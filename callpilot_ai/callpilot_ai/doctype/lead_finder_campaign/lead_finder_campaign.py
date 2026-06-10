import frappe
from frappe.model.document import Document

class LeadFinderCampaign(Document):
    def after_insert(self):
        # Automatically start scraping when the campaign is saved
        from callpilot_ai.api.scraper import trigger_scrape
        frappe.db.set_value("Lead Finder Campaign", self.name, "status", "Pending")
        trigger_scrape(self.name)
