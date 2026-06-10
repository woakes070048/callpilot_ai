frappe.ui.form.on('Lead Finder Settings', {
    scraper_engine: function(frm) {
        if (frm.doc.scraper_engine === 'Desktop Scraper') {
            frappe.msgprint({
                title: __('Free Desktop Scraping'),
                indicator: 'green',
                message: __('To extract Google Maps leads for free without paying API fees, you must use a local desktop software.<br><br><b>Step 1:</b> Download <a href="https://wasender.me" target="_blank" style="color: blue; text-decoration: underline;">WA Sender Desktop</a>.<br><b>Step 2:</b> Run the Google Maps Extractor inside WA Sender.<br><b>Step 3:</b> Export your results to a CSV file.<br><b>Step 4:</b> Use the standard ERPNext Data Import tool to upload your CSV into the Lead List.<br><br><i>After importing, you can select the leads and click <b>Run AI Analysis</b>!</i>')
            });
        }
    }
});
