# Copyright (c) 2024, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TSCAwningPricing(Document):
	def validate(self):
		doc = frappe.get_doc("Item", self.awning_item)
		if (doc.default_bom):
			pass
		else:
			frappe.throw("Please Select Valid Awning Item")
   
		doc1 = frappe.get_doc("Item", self.canopy_item)
		if (doc1.default_bom):
			pass
		else:
			frappe.throw("Please Select Valid Canopy Item")

		self.total_cost = self.awning_bom_cost + self.canopy_bom_cost
		self.total_selling = (self.awning_bom_cost + self.canopy_bom_cost) * self.total_selling_multiplier
		self.product_description = "Awning Item"+" - "+doc.description+"\n"+"Canopy Item"+" - "+doc1.description
  
	 
@frappe.whitelist()
def awning_item_cost(awning_item):
	doc = frappe.get_doc("Item", awning_item)
	if (doc.default_bom):
		bom = doc.default_bom
		bom_doc = frappe.get_doc("BOM", bom)
		cost = bom_doc.total_cost
		return cost
	else:
		frappe.throw("This Item Has No BOM")



@frappe.whitelist()
def canopy_item_cost(canopy_item):
	doc = frappe.get_doc("Item", canopy_item)
	if (doc.default_bom):
		bom = doc.default_bom
		bom_doc = frappe.get_doc("BOM", bom)
		cost = bom_doc.total_cost
		return cost
	else:
		frappe.throw("This Item Has No BOM")