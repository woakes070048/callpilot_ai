frappe.listview_settings['Lead'] = {
    onload: function(listview) {
        listview.page.add_action_item(__("CallPilot AI Voice"), function() {
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
    }
};

