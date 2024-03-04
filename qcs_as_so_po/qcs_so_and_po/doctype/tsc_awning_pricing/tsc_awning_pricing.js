// Copyright (c) 2024, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.ui.form.on('TSC Awning Pricing', {
	awning_item: function(frm) {
		frappe.call({
            method: 'qcs_as_so_po.qcs_so_and_po.doctype.tsc_awning_pricing.tsc_awning_pricing.awning_item_cost',
            args: {
                "awning_item": cur_frm.doc.awning_item,
            },
			callback: function(r) {
				frm.set_value("awning_bom_cost", r.message);
			}
        });
	},
	canopy_item: function(frm) {
		frappe.call({
            method: 'qcs_as_so_po.qcs_so_and_po.doctype.tsc_awning_pricing.tsc_awning_pricing.canopy_item_cost',
            args: {
                "canopy_item": cur_frm.doc.canopy_item,
            },
			callback: function(r) {
				frm.set_value("canopy_bom_cost", r.message);
			}
        });
	}
});
