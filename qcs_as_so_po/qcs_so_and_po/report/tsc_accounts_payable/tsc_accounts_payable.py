# Copyright (c) 2024, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):

	columns = [
		{
			"fieldname": "supplier",
			"label": ("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
		},
		{
			"fieldname": "advance_amount",
			"label": ("Advance Amount"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "purchase_order_amount",
			"label": ("Purchase Order Amount"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "invoiced_amount",
			"label": ("Invoiced Amount"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "paid_amount",
			"label": ("Paid Amount"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "credit_amount",
			"label": ("Credit Note"),
			"fieldtype": "Currency",
		},
		# {
		# 	"fieldname": "po_outstanding",
		# 	"label": ("PO Outstanding"),
		# 	"fieldtype": "Currency",
		# },
		# {
		# 	"fieldname": "invoiced_outstanding",
		# 	"label": ("Invoiced Outstanding"),
		# 	"fieldtype": "Currency",
		# },
		{
			"fieldname": "final_payable",
			"label": ("Final Payable"),
			"fieldtype": "Currency",
		},
	]
	return columns



def get_data(filters):
	data = []

	query_filters_c = []
	if filters.get("supplier"):
		query_filters_c.append(["name", "=", filters.get("supplier")])
	query_filters_c.append(["disabled", "=", 0])

	supplier = frappe.get_all("Supplier", filters=query_filters_c, fields=["name"])
	for k in supplier:
		sup = k.get("name")
		sup_data = {"supplier": sup}

		query_filters0 = []
		query_filters0.append(["company", "=", filters.get("company")])
		query_filters0.append(["transaction_date", ">=", filters.get("from_date")])
		query_filters0.append(["transaction_date", "<=", filters.get("to_date")])
		query_filters0.append(["status", "in", ["To Receive and Bill", "To Bill", "On Hold"]])
		query_filters0.append(["supplier", "=", sup])
		query_filters0.append(["docstatus", "=", 1])
	
		advance = [0]
		po_amount_based_on_perbilled = [0]
		po_ind = frappe.get_all("Purchase Order", filters=query_filters0, fields=["supplier", "grand_total", "per_billed", "advance_paid"])
		if po_ind:
			
			for po in po_ind:
				advance.append(po.get("advance_paid"))
				po_grand_amount = po.get("grand_total") * (1 - po.get("per_billed") / 100)
				po_amount_based_on_perbilled.append(po_grand_amount)
		sup_data["advance_amount"] = sum(advance)
		sup_data["purchase_order_amount"] = sum(po_amount_based_on_perbilled)

# Purchase invoice

		query_filters1 = []
		query_filters1.append(["company", "=", filters.get("company")])
		query_filters1.append(["posting_date", ">=", filters.get("from_date")])
		query_filters1.append(["posting_date", "<=", filters.get("to_date")])
		query_filters1.append(["supplier", "=", sup])
		query_filters1.append(["docstatus", "=", 1])

		inv_amount=[]
		pi = frappe.get_all("Purchase Invoice", filters=query_filters1, fields=["supplier", "sum(grand_total) as grand_total"], group_by="supplier")
		if pi:
			for j in pi:
				sup_data["invoiced_amount"] = j.get("grand_total")
				inv_amount.append(j.get("grand_total"))
		else:
			sup_data["invoiced_amount"] = 0
			inv_amount.append(0)
	#  return 
	
		query_filters2 = []
		query_filters2.append(["company", "=", filters.get("company")])
		query_filters2.append(["posting_date", ">=", filters.get("from_date")])
		query_filters2.append(["posting_date", "<=", filters.get("to_date")])
		query_filters2.append(["supplier", "=", sup])
		query_filters2.append(["docstatus", "=", 1])
		query_filters2.append(["status", "=", "Return"])

		pi_return = frappe.get_all("Purchase Invoice", filters=query_filters2, fields=["supplier", "sum(grand_total) as grand_total"], group_by="supplier")
		if pi_return:
			for j1 in pi_return:
				sup_data["credit_amount"] = -(j1.get("grand_total"))
		else:
			sup_data["credit_amount"] = 0
   
# payment entry

		query_filters3 = []
		query_filters3.append(["company", "=", filters.get("company")])
		query_filters3.append(["posting_date", ">=", filters.get("from_date")])
		query_filters3.append(["posting_date", "<=", filters.get("to_date")])
		query_filters3.append(["party_type", "=", "supplier"])
		query_filters3.append(["party", "=", sup])
		query_filters3.append(["docstatus", "=", 1])

		pay_amount=[]
		pay = frappe.get_all("Payment Entry", filters=query_filters3, fields=["party", "sum(paid_amount) as paid_amount"], group_by="party")
		if pay:
			for p in pay:
				sup_data["paid_amount"] = p.get("paid_amount")
				pay_amount.append(p.get("paid_amount"))
		else:
			sup_data["paid_amount"] = 0
			pay_amount.append(0)
# Totals

		sup_data["invoiced_outstanding"] = inv_amount[0] - pay_amount[0]
		# sup_data["so_outstanding"] = sum(po_amount_based_on_perbilled) - pay_amount[0]
		sup_data["final_payable"] = sup_data["purchase_order_amount"] + sup_data["invoiced_amount"] - sup_data["credit_amount"] - sup_data["paid_amount"]
		
		data.append(sup_data)
			
	return data
		
		
 
	
		
	