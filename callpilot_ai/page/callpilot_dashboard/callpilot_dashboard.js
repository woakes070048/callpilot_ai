frappe.pages['callpilot_dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'CallPilot AI Dashboard',
        single_column: true
    });
    
    .appendTo(page.main);
    
    frappe.call({
        method: "callpilot_ai.page.callpilot_dashboard.callpilot_dashboard.get_dashboard_data",
        callback: function(r) {
            if(r.message) {
                render_charts(r.message);
            }
        }
    });
}

function render_charts(data) {
    new frappe.Chart("#outcomes-chart", {
        data: {
            labels: ["Interested", "Not Interested", "Failed"],
            datasets: [
                { values: [data.interested, data.not_interested, data.failed] }
            ]
        },
        title: "Call Outcomes",
        type: 'pie',
        height: 300,
        colors: ['#28a745', '#dc3545', '#ffc107']
    });
    
    new frappe.Chart("#roi-chart", {
        data: {
            labels: ["Leads Scraped", "Called", "Interested (Booked)"],
            datasets: [
                { values: [data.total_leads, data.called, data.interested] }
            ]
        },
        title: "Conversion Funnel",
        type: 'bar',
        height: 300,
        colors: ['#007bff']
    });
}
