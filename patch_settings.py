import json

path = 'callpilot_ai/callpilot_ai/doctype/lead_finder_settings/lead_finder_settings.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update Scraper Engine options
for field in data['fields']:
    if field['fieldname'] == 'scraper_engine':
        field['options'] = 'Apify\nOutscraper\nDesktop Scraper'
        break

# Add new fields
data['fields'].insert(3, {
    'fieldname': 'outscraper_api_key',
    'fieldtype': 'Small Text',
    'label': 'Outscraper API Key',
    'depends_on': 'eval:doc.scraper_engine=="Outscraper"'
})

data['fields'].insert(4, {
    'fieldname': 'scraper_markup_margin',
    'fieldtype': 'Percent',
    'label': 'Scraper Markup Margin (%)',
    'description': 'Enter the percentage markup to charge your clients for lead scraping (e.g., 20 for a 20% profit margin).',
    'default': '20'
})

data['field_order'] = [
    'scraper_engine',
    'apify_source_platform',
    'apify_api_key',
    'outscraper_api_key',
    'scraper_markup_margin',
    'llm_provider',
    'llm_api_key',
    'bolna_api_key',
    'bolna_agent_id'
]

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
