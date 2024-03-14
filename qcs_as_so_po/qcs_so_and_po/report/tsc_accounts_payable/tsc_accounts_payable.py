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
		{
			"fieldname": "po_outstanding",
			"label": ("PO Outstanding"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "invoiced_outstanding",
			"label": ("Invoiced Outstanding"),
			"fieldtype": "Currency",
		},
	]
	return columns


def get_data(filters):
	data = []
	query_filters = []
	query_filters.append(["company", "=", filters.get("company")])
	query_filters.append(["transaction_date", ">=", filters.get("from_date")])
	query_filters.append(["transaction_date", "<=", filters.get("to_date")])
	if filters.get("supplier"):
		query_filters.append(["supplier", "=", filters.get("supplier")])
	query_filters.append(["docstatus", "=", 1])

	doc = frappe.get_all("Purchase Order", filters=query_filters, fields=["supplier", "sum(grand_total) as grand_total", "sum(advance_paid) as advance_paid"], group_by="supplier")
	if (doc):
		for i in doc:
			cus_data = {"supplier": i.get("supplier"), "purchase_order_amount": i.get("grand_total"), "advance_amount": i.get("advance_paid")}

			query_filters1 = []
			query_filters1.append(["company", "=", filters.get("company")])
			query_filters1.append(["posting_date", ">=", filters.get("from_date")])
			query_filters1.append(["posting_date", "<=", filters.get("to_date")])
			query_filters1.append(["supplier", "=", i.get("supplier")])
			query_filters1.append(["docstatus", "=", 1])
   
			pi_amount=[]
			pi = frappe.get_all("Purchase Invoice", filters=query_filters1, fields=["supplier", "sum(grand_total) as grand_total"], group_by="supplier")
			if pi:
				for j in pi:
					cus_data["invoiced_amount"] = j.get("grand_total")
					pi_amount.append(j.get("grand_total"))
			else:
				cus_data["invoiced_amount"] = 0
				pi_amount.append(0)
    
			query_filters2 = []
			query_filters2.append(["company", "=", filters.get("company")])
			query_filters2.append(["posting_date", ">=", filters.get("from_date")])
			query_filters2.append(["posting_date", "<=", filters.get("to_date")])
			query_filters2.append(["supplier", "=", i.get("supplier")])
			query_filters2.append(["docstatus", "=", 1])
			query_filters2.append(["status", "=", "Return"])
   
			pi_return = frappe.get_all("Purchase Invoice", filters=query_filters2, fields=["supplier", "sum(grand_total) as grand_total"], group_by="supplier")
			if pi_return:
				for j1 in pi_return:
					cus_data["credit_amount"] = -(j1.get("grand_total"))
			else:
				cus_data["credit_amount"] = 0
    
			query_filters3 = []
			query_filters3.append(["company", "=", filters.get("company")])
			query_filters3.append(["posting_date", ">=", filters.get("from_date")])
			query_filters3.append(["posting_date", "<=", filters.get("to_date")])
			query_filters3.append(["party_type", "=", "Supplier"])
			query_filters3.append(["party", "=", i.get("supplier")])
			query_filters3.append(["docstatus", "=", 1])
   
			pay_amount=[]
			pay = frappe.get_all("Payment Entry", filters=query_filters3, fields=["party", "sum(paid_amount) as paid_amount"], group_by="party")
			if pay:
				for p in pay:
					cus_data["paid_amount"] = p.get("paid_amount")
					pay_amount.append(p.get("paid_amount"))
			else:
				cus_data["paid_amount"] = 0
				pay_amount.append(0)
    
			cus_data["invoiced_outstanding"] = pi_amount[0] - pay_amount[0]
			cus_data["po_outstanding"] = i.get("grand_total") - pay_amount[0]

			data.append(cus_data)
					
	return data
		
 
	
		
	