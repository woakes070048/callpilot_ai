frappe.listview_settings['Lead'] = {
    onload: function(listview) {
        listview.page.add_action_item("<b>📞 CallPilot AI Voice</b>", function() {
            const selected = listview.get_checked_items();
            if (selected.length === 0) return;
            const lead_names = selected.map(item => item.name);
            frappe.call({
                method: "callpilot_ai.api.bolna.trigger_bulk_calls",
                args: { lead_names: lead_names },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__("CallPilot AI Voice job queued for " + selected.length + " leads."));
                        listview.clear_checked_items();
                    }
                }
            });
        });

        listview.page.add_action_item("<b>🧠 Run AI Analysis</b>", function() {
            const selected = listview.get_checked_items();
            if (selected.length === 0) return;
            const lead_names = selected.map(item => item.name);
            
            frappe.prompt([
                {
                    label: 'AI Qualification Prompt',
                    fieldname: 'ai_prompt',
                    fieldtype: 'Small Text',
                    reqd: 1,
                    description: "Example: Only accept companies that mention industrial services on their website."
                }
            ], function(values){
                frappe.call({
                    method: "callpilot_ai.api.bulk_analyzer.trigger_bulk_analysis",
                    args: { 
                        lead_names: lead_names,
                        ai_prompt: values.ai_prompt
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__("Bulk AI Analysis started for " + selected.length + " leads."));
                            listview.clear_checked_items();
                        }
                    }
                });
            }, 'AI Lead Analyzer', 'Start Analysis');
        });
    }
};
