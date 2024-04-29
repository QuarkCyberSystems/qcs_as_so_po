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
			"fieldname": "voucher_type",
			"label": ("Type of Voucher"),
			"fieldtype": "Data",
			"width": 300,
		},
		{
			"fieldname": "submit",
			"label": ("Submitted Document Count"),
			"fieldtype": "Data",
			"width": 300,
		},
		{
			"fieldname": "cancel",
			"label": ("Cancelled Document Count"),
			"fieldtype": "Data",
			"width": 300,
		},
	]
	frappe.errprint(columns)
	return columns


def get_data(filters):
    
	data = []
 
	query_filters1 = []
	query_filters1.append(["company", "=", filters["company"]])
	query_filters1.append(["posting_date", ">=", filters["from_date"]])
	query_filters1.append(["posting_date", "<=", filters["to_date"]])
	query_filters1.append(["docstatus", "=", 1])
 
	query_filters2 = []
	query_filters2.append(["company", "=", filters["company"]])
	query_filters2.append(["posting_date", ">=", filters["from_date"]])
	query_filters2.append(["posting_date", "<=", filters["to_date"]])
	query_filters2.append(["docstatus", "=", 2])
  
	query_filters3 = []
	query_filters3.append(["company", "=", filters["company"]])
	query_filters3.append(["transaction_date", ">=", filters["from_date"]])
	query_filters3.append(["transaction_date", "<=", filters["to_date"]])
	query_filters3.append(["docstatus", "=", 1])
 
	query_filters4 = []
	query_filters4.append(["company", "=", filters["company"]])
	query_filters4.append(["transaction_date", ">=", filters["from_date"]])
	query_filters4.append(["transaction_date", "<=", filters["to_date"]])
	query_filters4.append(["docstatus", "=", 2])
 
# sales order
	so = frappe.get_all("Sales Order", filters=query_filters3)
	so1 = frappe.get_all("Sales Order", filters=query_filters4)
	data.append({"voucher_type": "Sales Order", "submit":len(so), "cancel": len(so1)})
 
# sales invoice
	si = frappe.get_all("Sales Invoice", filters=query_filters1)
	si1 = frappe.get_all("Sales Invoice", filters=query_filters2)
	data.append({"voucher_type": "Sales Invoice", "submit":len(si), "cancel": len(si1)})
 
# sales invoice
	dn = frappe.get_all("Delivery Note", filters=query_filters1)
	dn1 = frappe.get_all("Delivery Note", filters=query_filters2)
	data.append({"voucher_type": "Delivery Note", "submit":len(dn), "cancel": len(dn1)})
 
# Purchase order
	po = frappe.get_all("Purchase Order", filters=query_filters3)
	po1 = frappe.get_all("Purchase Order", filters=query_filters4)
	data.append({"voucher_type": "Purchase Order", "submit":len(po), "cancel": len(po1)})
 
# Purchase invoice
	pi = frappe.get_all("Purchase Invoice", filters=query_filters1)
	pi1 = frappe.get_all("Purchase Invoice", filters=query_filters2)
	data.append({"voucher_type": "Purchase Invoice", "submit":len(pi), "cancel": len(pi1)})
 
# Purchase Receipt
	pr = frappe.get_all("Purchase Receipt", filters=query_filters1)
	pr1 = frappe.get_all("Purchase Receipt", filters=query_filters2)
	data.append({"voucher_type": "Purchase Receipt", "submit":len(pr), "cancel": len(pr1)})
 
# Payment Entry
	pe = frappe.get_all("Payment Entry", filters=query_filters1)
	pe1 = frappe.get_all("Payment Entry", filters=query_filters2)
	data.append({"voucher_type": "Payment Entry", "submit":len(pe), "cancel": len(pe1)})
 
# Stock Entry
	se = frappe.get_all("Stock Entry", filters=query_filters1)
	se1 = frappe.get_all("Stock Entry", filters=query_filters2)
	data.append({"voucher_type": "Stock Entry", "submit":len(se), "cancel": len(se1)})
 
# Material Request
	mr = frappe.get_all("Material Request", filters=query_filters3)
	mr1 = frappe.get_all("Material Request", filters=query_filters4)
	data.append({"voucher_type": "Material Request", "submit":len(mr), "cancel": len(mr1)})
 
# Work Order
	wo = frappe.get_all("Work Order", filters={"company": filters.get("company"), "expected_delivery_date":["between", (filters.get("from_date"), filters.get("to_date"))], "docstatus": 1})
	wo1 = frappe.get_all("Work Order", filters={"company": filters.get("company"), "expected_delivery_date":["between", (filters.get("from_date"), filters.get("to_date"))], "docstatus": 2})
	data.append({"voucher_type": "Work Order", "submit":len(wo), "cancel": len(wo1)})
 
# Job Card
	jc = frappe.get_all("Job Card", filters=query_filters1)
	jc1 = frappe.get_all("Job Card", filters=query_filters2)
	data.append({"voucher_type": "Job Card", "submit":len(jc), "cancel": len(jc1)})
 
# GL Entry
	gl = frappe.get_all("GL Entry", filters=query_filters1)
	gl1 = frappe.get_all("GL Entry", filters=query_filters2)
	data.append({"voucher_type": "GL Entry", "submit":len(gl), "cancel": len(gl1)})
 
# Journal Entry
	jv_type = ["Journal Entry", "Inter Company Journal Entry", "Bank Entry", "Cash Entry", "Credit Card Entry", "Debit Note", "Credit Note", "Contra Entry", "Excise Entry", "Write Off Entry", "Opening Entry", "Depreciation Entry", "Exchange Rate Revaluation", "Exchange Gain Or Loss", "Deferred Revenue", "Deferred Expense"]
	for i in jv_type:
		jv = frappe.get_all("Journal Entry", filters={"company": filters.get("company"), "posting_date":["between", (filters.get("from_date"), filters.get("to_date"))], "docstatus": 1, "voucher_type": i})
		jv1 = frappe.get_all("Journal Entry", filters={"company": filters.get("company"), "posting_date":["between", (filters.get("from_date"), filters.get("to_date"))], "docstatus": 2, "voucher_type": i})
		data.append({"voucher_type": i, "submit":len(jv), "cancel": len(jv1)})
 
# Ledger
	ledger_count = frappe.db.count('Account', filters={'is_group': 0, "company": filters.get("company"), 'disabled': 0})
	ledger_count1 = frappe.db.count('Account', filters={'is_group': 0, "company": filters.get("company"), 'disabled': 1})
	data.append({"voucher_type": "Ledger", "submit":ledger_count, "cancel": ledger_count1})
 
# Ledger Group
	ledger_count_1 = frappe.db.count('Account', filters={'is_group': 1, "company": filters.get("company"), 'disabled': 0})
	ledger_count1_1 = frappe.db.count('Account', filters={'is_group': 1, "company": filters.get("company"), 'disabled': 1})
	data.append({"voucher_type": "Ledger Group", "submit":ledger_count_1, "cancel": ledger_count1_1})
 
# Cost Center
	cost_center = frappe.db.count('Cost Center', filters={'disabled': 0, "company": filters.get("company"), 'is_group': 0})
	cost_center1 = frappe.db.count('Cost Center', filters={'disabled': 1, "company": filters.get("company"), 'is_group': 0})
	data.append({"voucher_type": "Cost Center", "submit":cost_center, "cancel": cost_center1})
 
# Cost Center Group
	cost_center = frappe.db.count('Cost Center', filters={'disabled': 0, "company": filters.get("company"), 'is_group': 1})
	cost_center1 = frappe.db.count('Cost Center', filters={'disabled': 1, "company": filters.get("company"), 'is_group': 1})
	data.append({"voucher_type": "Cost Center Group", "submit":cost_center, "cancel": cost_center1})
 
# Warehouse
	warehouse_count = frappe.db.count('Warehouse', filters={'disabled': 0, 'company': filters.get("company"), 'is_group': 0})
	warehouse_count1 = frappe.db.count('Warehouse', filters={'disabled': 1, 'company': filters.get("company"), 'is_group': 0})
	data.append({"voucher_type": "Warehouse", "submit":warehouse_count, "cancel": warehouse_count1})
 
# Warehouse Group
	warehouse_count = frappe.db.count('Warehouse', filters={'disabled': 0, 'company': filters.get("company"), 'is_group': 1})
	warehouse_count1 = frappe.db.count('Warehouse', filters={'disabled': 1, 'company': filters.get("company"), 'is_group': 1})
	data.append({"voucher_type": "Warehouse Group", "submit":warehouse_count, "cancel": warehouse_count1})

# Stock Items
	item = frappe.db.count('Item', filters={'is_stock_item': 1, 'disabled': 0})
	item1 = frappe.db.count('Item', filters={'is_stock_item': 1, 'disabled': 1})
	data.append({"voucher_type": "Stock Items", "submit":item, "cancel": item1})
 
	return data

