import frappe
from frappe.model.document import Document

class LeadFinderCampaign(Document):
    def before_save(self):
        if self.status == "Draft":
            self.status = "Pending"
            self.flags.trigger_scrape = True
            
    def on_update(self):
        if self.flags.trigger_scrape:
            self.flags.trigger_scrape = False
            from callpilot_ai.api.scraper import trigger_scrape
            trigger_scrape(self.name)
