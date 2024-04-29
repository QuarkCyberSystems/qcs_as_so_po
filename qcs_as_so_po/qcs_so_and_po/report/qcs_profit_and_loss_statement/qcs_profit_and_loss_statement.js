// Copyright (c) 2024, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt


frappe.query_reports["QCS Profit and Loss Statement"] = $.extend({}, erpnext.financial_statements);

erpnext.utils.add_dimensions("QCS Profit and Loss Statement", 10);

frappe.query_reports["QCS Profit and Loss Statement"]["filters"].push({
	fieldname: "selected_view",
	label: __("Select View"),
	fieldtype: "Select",
	options: [
		{ value: "Report", label: __("Report View") },
		{ value: "Growth", label: __("Growth View") },
		{ value: "Margin", label: __("Margin View") },
	],
	default: "Report",
	reqd: 1,
});

frappe.query_reports["QCS Profit and Loss Statement"]["filters"].push({
	fieldname: "accumulated_values",
	label: __("Accumulated Values"),
	fieldtype: "Check",
	default: 1,
});

