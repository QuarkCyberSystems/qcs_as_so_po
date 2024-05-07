# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt, today
from pypika.terms import ExistsCriterion

from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_pos_reserved_qty
from erpnext.stock.utils import (
	is_reposting_item_valuation_in_progress,
	update_included_uom_in_report,
)


def execute(filters=None):
	is_reposting_item_valuation_in_progress()
	filters = frappe._dict(filters or {})
	include_uom = filters.get("include_uom")
	columns = get_columns()
	bin_list = get_bin_list(filters)
	item_map = get_item_map(filters.get("item_code"), include_uom)

	warehouse_company = {}
	data = []
	conversion_factors = []
	for bin in bin_list:
		item = item_map.get(bin.item_code)

		if not item:
			# likely an item that has reached its end of life
			continue

		# item = item_map.setdefault(bin.item_code, get_item(bin.item_code))
		company = warehouse_company.setdefault(
			bin.warehouse, frappe.db.get_value("Warehouse", bin.warehouse, "company")
		)

		if filters.brand and filters.brand != item.brand:
			continue

		elif filters.item_group and filters.item_group != item.item_group:
			continue

		elif filters.company and filters.company != company:
			continue

		re_order_level = re_order_qty = 0

		for d in item.get("reorder_levels"):
			if d.warehouse == bin.warehouse:
				re_order_level = d.warehouse_reorder_level
				re_order_qty = d.warehouse_reorder_qty

		shortage_qty = 0
		if (re_order_level or re_order_qty) and re_order_level > bin.projected_qty:
			shortage_qty = re_order_level - flt(bin.projected_qty)

		reserved_qty_for_pos = get_pos_reserved_qty(bin.item_code, bin.warehouse)
		if reserved_qty_for_pos:
			bin.projected_qty -= reserved_qty_for_pos

		data.append(
			[
				item.name,
				item.item_name,
				item.description,
				item.item_group,
				item.brand,
				bin.warehouse,
				item.stock_uom,
				bin.actual_qty,
				bin.planned_qty,
				bin.indented_qty,
				bin.ordered_qty,
				bin.reserved_qty,
				bin.reserved_qty_for_production,
				bin.reserved_qty_for_production_plan,
				bin.reserved_qty_for_sub_contract,
				reserved_qty_for_pos,
				bin.projected_qty,
				re_order_level,
				re_order_qty,
				shortage_qty,
			]
		)

		if include_uom:
			conversion_factors.append(item.conversion_factor)

	update_included_uom_in_report(columns, data, include_uom, conversion_factors)
	final_data = []
 
	# Sales Order
 
	so_items = frappe.get_all("Sales Order Item",fields=["parent", "item_code"])
	parent_sales_orders = set(item["parent"] for item in so_items)

	filtered_parent_sales_orders = frappe.get_all("Sales Order", filters={"name": ["in", list(parent_sales_orders)], "docstatus": 1, "status": ["not in", ["Completed", "To Bill", "Closed"]]}, fields=["name"])
	filtered_parent_sales_orders_set = set(so["name"] for so in filtered_parent_sales_orders)

	so_dict = {}
	for so_item in so_items:
		if so_item["item_code"] not in so_dict:
			so_dict[so_item["item_code"]] = set()
		if so_item["parent"] in filtered_parent_sales_orders_set:
			so_dict[so_item["item_code"]].add(so_item["parent"])
   
	#  Work Order
 
	wo_items = frappe.get_all("Work Order Item", fields=["parent", "item_code"])
	parent_work_orders = set(item["parent"] for item in wo_items)

	filtered_parent_work_orders = frappe.get_all("Work Order", filters={"name": ["in", list(parent_work_orders)], "status": ["in", ["In Process", "Not Started"]]}, fields=["name"])
	filtered_parent_work_orders_set = set(wo["name"] for wo in filtered_parent_work_orders)

	wo_dict = {}
	for wo_item in wo_items:
		if wo_item["item_code"] not in wo_dict:
			wo_dict[wo_item["item_code"]] = set()
		if wo_item["parent"] in filtered_parent_work_orders_set:
			wo_dict[wo_item["item_code"]].add(wo_item["parent"])
 
	# Subcontracting Order
 
	subcon_items = frappe.get_all("Subcontracting Order Supplied Item", fields=["parent", "main_item_code"])
	parent_subcon_orders = set(item["parent"] for item in subcon_items)

	filtered_parent_subcon_orders = frappe.get_all("Subcontracting Order",
		filters={"name": ["in", list(parent_subcon_orders)], "docstatus": 1, "status": ["not in", ["Completed", "Closed"]]},
		fields=["name"])
	filtered_parent_subcon_orders_set = set(so["name"] for so in filtered_parent_subcon_orders)

	subcon_dict = {}
	for subcon_item in subcon_items:
		if subcon_item["main_item_code"] not in subcon_dict:
			subcon_dict[subcon_item["main_item_code"]] = set()
		if subcon_item["parent"] in filtered_parent_subcon_orders_set:
			subcon_dict[subcon_item["main_item_code"]].add(subcon_item["parent"])
 
	# Process data to insert Sales Order names
	final_data = []
	for i in data:
		if i[11] > 0:
			item_code = i[0]
			sales_orders = so_dict.get(item_code, set())
			i.insert(12, ', '.join(sales_orders))
		else:
			i.insert(12, "")
		if i[13] > 0:
			item_code = i[0]
			work_orders = wo_dict.get(item_code, set())
			i.insert(14, ', '.join(work_orders))
		else:
			i.insert(14, "")
		if i[16] > 0:
			main_item_code = i[0]
			subcon_orders = subcon_dict.get(main_item_code, set())
			i.insert(17, ', '.join(subcon_orders))
		else:
			i.insert(17, "")
		final_data.append(i)
  
	return columns, final_data


def get_columns():
	return [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 100},
		{"label": _("Description"), "fieldname": "description", "width": 200},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100,
		},
		{
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Link",
			"options": "Brand",
			"width": 100,
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120,
		},
		{
			"label": _("UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 100,
		},
		{
			"label": _("Actual Qty"),
			"fieldname": "actual_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Planned Qty"),
			"fieldname": "planned_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Requested Qty"),
			"fieldname": "indented_qty",
			"fieldtype": "Float",
			"width": 110,
			"convertible": "qty",
		},
		{
			"label": _("Ordered Qty"),
			"fieldname": "ordered_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Reserved Qty"),
			"fieldname": "reserved_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Small Text",
			"width": 200,
		},
		{
			"label": _("Reserved for Production"),
			"fieldname": "reserved_qty_for_production",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Work Order"),
			"fieldname": "work_order",
			"fieldtype": "Small Text",
			"width": 200,
		},
		{
			"label": _("Reserved for Production Plan"),
			"fieldname": "reserved_qty_for_production_plan",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Reserved for Sub Contracting"),
			"fieldname": "reserved_qty_for_sub_contract",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Subcontracting Order"),
			"fieldname": "subcontracting_order",
			"fieldtype": "Small Text",
			"width": 200,
		},
		{
			"label": _("Reserved for POS Transactions"),
			"fieldname": "reserved_qty_for_pos",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Projected Qty"),
			"fieldname": "projected_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Reorder Level"),
			"fieldname": "re_order_level",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Reorder Qty"),
			"fieldname": "re_order_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
		{
			"label": _("Shortage Qty"),
			"fieldname": "shortage_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
		},
	]


def get_bin_list(filters):
	bin = frappe.qb.DocType("Bin")
	query = (
		frappe.qb.from_(bin)
		.select(
			bin.item_code,
			bin.warehouse,
			bin.actual_qty,
			bin.planned_qty,
			bin.indented_qty,
			bin.ordered_qty,
			bin.reserved_qty,
			bin.reserved_qty_for_production,
			bin.reserved_qty_for_sub_contract,
			bin.reserved_qty_for_production_plan,
			bin.projected_qty,
		)
		.orderby(bin.item_code, bin.warehouse)
	)

	if filters.item_code:
		query = query.where(bin.item_code == filters.item_code)

	if filters.warehouse:
		warehouse_details = frappe.db.get_value(
			"Warehouse", filters.warehouse, ["lft", "rgt"], as_dict=1
		)

		if warehouse_details:
			wh = frappe.qb.DocType("Warehouse")
			query = query.where(
				ExistsCriterion(
					frappe.qb.from_(wh)
					.select(wh.name)
					.where(
						(wh.lft >= warehouse_details.lft)
						& (wh.rgt <= warehouse_details.rgt)
						& (bin.warehouse == wh.name)
					)
				)
			)

	bin_list = query.run(as_dict=True)

	return bin_list


def get_item_map(item_code, include_uom):
	"""Optimization: get only the item doc and re_order_levels table"""

	bin = frappe.qb.DocType("Bin")
	item = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(item)
		.select(item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom)
		.where(
			(item.is_stock_item == 1)
			& (item.disabled == 0)
			& (
				(item.end_of_life > today()) | (item.end_of_life.isnull()) | (item.end_of_life == "0000-00-00")
			)
			& (ExistsCriterion(frappe.qb.from_(bin).select(bin.name).where(bin.item_code == item.name)))
		)
	)

	if item_code:
		query = query.where(item.item_code == item_code)

	if include_uom:
		ucd = frappe.qb.DocType("UOM Conversion Detail")
		query = query.left_join(ucd).on((ucd.parent == item.name) & (ucd.uom == include_uom))

	items = query.run(as_dict=True)

	ir = frappe.qb.DocType("Item Reorder")
	query = frappe.qb.from_(ir).select("*")

	if item_code:
		query = query.where(ir.parent == item_code)

	reorder_levels = frappe._dict()
	for d in query.run(as_dict=True):
		if d.parent not in reorder_levels:
			reorder_levels[d.parent] = []

		reorder_levels[d.parent].append(d)

	item_map = frappe._dict()
	for item in items:
		item["reorder_levels"] = reorder_levels.get(item.name) or []
		item_map[item.name] = item

	return item_map
