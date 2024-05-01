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
			"fieldname": "customer",
			"label": ("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
		},
		{
			"fieldname": "advance_amount",
			"label": ("Advance Amount"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "sales_order_amount",
			"label": ("Sales Order Amount"),
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
			"fieldname": "so_outstanding",
			"label": ("SO Outstanding"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "invoiced_outstanding",
			"label": ("Invoiced Outstanding"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "open_so",
			"label": ("Open SO"),
			"fieldtype": "Currency",
		},
		{
			"fieldname": "final_receivable",
			"label": ("Final Receivable"),
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
	#query_filters.append(["per_billed", "<", 100])
	if filters.get("customer"):
		query_filters.append(["customer", "=", filters.get("customer")])
	query_filters.append(["docstatus", "=", 1])

	doc = frappe.get_all("Sales Order", filters=query_filters, fields=["customer", "sum(grand_total) as grand_total", "sum(advance_paid) as advance_paid"], group_by="customer")
	if (doc):
		for i in doc:
			cus_data = {"customer": i.get("customer"), "sales_order_amount": i.get("grand_total"), "advance_amount": i.get("advance_paid")}

			query_filters1 = []
			query_filters1.append(["company", "=", filters.get("company")])
			query_filters1.append(["posting_date", ">=", filters.get("from_date")])
			query_filters1.append(["posting_date", "<=", filters.get("to_date")])
			query_filters1.append(["customer", "=", i.get("customer")])
			query_filters1.append(["docstatus", "=", 1])
   
			inv_amount=[]
			si = frappe.get_all("Sales Invoice", filters=query_filters1, fields=["customer", "sum(grand_total) as grand_total"], group_by="customer")
			if si:
				for j in si:
					cus_data["invoiced_amount"] = j.get("grand_total")
					inv_amount.append(j.get("grand_total"))
			else:
				cus_data["invoiced_amount"] = 0
				inv_amount.append(0)
    
			query_filters2 = []
			query_filters2.append(["company", "=", filters.get("company")])
			query_filters2.append(["posting_date", ">=", filters.get("from_date")])
			query_filters2.append(["posting_date", "<=", filters.get("to_date")])
			query_filters2.append(["customer", "=", i.get("customer")])
			query_filters2.append(["docstatus", "=", 1])
			query_filters2.append(["status", "=", "Return"])
   
			si_return = frappe.get_all("Sales Invoice", filters=query_filters2, fields=["customer", "sum(grand_total) as grand_total"], group_by="customer")
			if si_return:
				for j1 in si_return:
					cus_data["credit_amount"] = -(j1.get("grand_total"))
			else:
				cus_data["credit_amount"] = 0
    
			query_filters3 = []
			query_filters3.append(["company", "=", filters.get("company")])
			query_filters3.append(["posting_date", ">=", filters.get("from_date")])
			query_filters3.append(["posting_date", "<=", filters.get("to_date")])
			query_filters3.append(["party_type", "=", "Customer"])
			query_filters3.append(["party", "=", i.get("customer")])
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
    
			cus_data["invoiced_outstanding"] = inv_amount[0] - pay_amount[0]
			cus_data["so_outstanding"] = i.get("grand_total") - pay_amount[0]
			cus_data["open_so"] =  cus_data["sales_order_amount"] - cus_data["invoiced_amount"]
			cus_data["final_receivable"] = cus_data["open_so"] + cus_data["invoiced_amount"] - cus_data["credit_amount"] - cus_data["paid_amount"]
			
			data.append(cus_data)
					
	return data
		
 
	
		
	
