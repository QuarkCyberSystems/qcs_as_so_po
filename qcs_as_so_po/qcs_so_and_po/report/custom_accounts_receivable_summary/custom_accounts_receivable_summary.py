# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _, scrub
from frappe.utils import cint, flt
from datetime import datetime


from erpnext.accounts.party import get_partywise_advanced_payment_amount
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	return AccountsReceivableSummary(filters).run(args)


class AccountsReceivableSummary(ReceivablePayableReport):
	def run(self, args):
		self.party_type = args.get("party_type")
		self.party_naming_by = frappe.db.get_value(
			args.get("naming_by")[0], None, args.get("naming_by")[1]
		)
		self.get_columns()
		self.get_data(args)
		return self.columns, self.data

	def get_data(self, args):
		self.data = []
		self.receivables = ReceivablePayableReport(self.filters).run(args)[1]

		self.get_party_total(args)

		party_advance_amount = (
			get_partywise_advanced_payment_amount(
				self.party_type,
				self.filters.report_date,
				self.filters.show_future_payments,
				self.filters.company,
				party=self.filters.get(scrub(self.party_type)),
			)
			or {}
		)

		if self.filters.show_gl_balance:
			gl_balance_map = get_gl_balance(self.filters.report_date)

		for party, party_dict in self.party_total.items():
			if party_dict.outstanding == 0:
				continue

			row = frappe._dict()

			row.party = party
			if self.party_naming_by == "Naming Series":
				row.party_name = frappe.get_cached_value(
					self.party_type, party, scrub(self.party_type) + "_name"
				)

			row.update(party_dict)

			# Advance against party
			row.advance = party_advance_amount.get(party, 0)

			# In AR/AP, advance shown in paid columns,
			# but in summary report advance shown in separate column
			row.paid -= row.advance

			if self.filters.show_gl_balance:
				row.gl_balance = gl_balance_map.get(party)
				row.diff = flt(row.outstanding) - flt(row.gl_balance)

			if self.filters.show_future_payments:
				row.remaining_balance = flt(row.outstanding) - flt(row.future_amount)

			self.data.append(row)
   
		query_filters = []
		query_filters.append(["company", "=", self.filters.get("company")])
		query_filters.append(["transaction_date", "<=", self.filters.get("report_date")])
		query_filters.append(["docstatus", "=", 1])
		if self.filters.get("customer"):
			query_filters.append(["customer", "in", self.filters.get("customer")])
		if self.filters.get("cost_center"):
			query_filters.append(["cost_center", "=", self.filters.get("cost_center")])
		if self.filters.get("customer_group"):
			query_filters.append(["customer_group", "in", self.filters.get("customer_group")])
		if self.filters.get("sales_person"):
			query_filters.append(["employee", "=", self.filters.get("sales_person")])
		if self.filters.get("territory"):
			query_filters.append(["territory", "=", self.filters.get("territory")])
   # Initialize overall values
		overall_outstanding = 0.0
		overall_advance = 0.0
		overall_total_due = 0.0
		overall_range1 = 0.0
		overall_range2 = 0.0
		overall_range3 = 0.0
		overall_range4 = 0.0
		overall_range5 = 0.0
		

		doc = frappe.get_all("Sales Order", filters=query_filters, fields=["name", "customer", "grand_total", "advance_paid", "territory", "customer_group", "currency", "transaction_date"])
		today = datetime.today().date()
		for i in doc:
			sales_order_data = {}
			transaction_date = i.get("transaction_date") or today
			age = (today - transaction_date).days

			if age <= self.filters.get("range1"):
				sales_order_data["advance"] = i.get("advance_paid")
				sales_order_data["outstanding"] = i.get("grand_total")
				sales_order_data["total_due"] = i.get("grand_total")
				sales_order_data["range1"] = i.get("grand_total")
				sales_order_data["range2"] = sales_order_data["range3"] = sales_order_data["range4"] = sales_order_data["range5"] = 0.0
			elif age <= self.filters.get("range2"):
				sales_order_data["advance"] = 0.0
				sales_order_data["outstanding"] = i.get("grand_total")
				sales_order_data["total_due"] = i.get("grand_total")
				sales_order_data["range1"] = 0.0
				sales_order_data["range2"] = i.get("grand_total")
				sales_order_data["range3"] = sales_order_data["range4"] = sales_order_data["range5"] = 0.0
			elif age <= self.filters.get("range3"):
				sales_order_data["advance"] = 0.0
				sales_order_data["outstanding"] = i.get("grand_total")
				sales_order_data["total_due"] = i.get("grand_total")
				sales_order_data["range1"] = sales_order_data["range2"] = 0.0
				sales_order_data["range3"] = i.get("grand_total")
				sales_order_data["range4"] = sales_order_data["range5"] = 0.0
			elif age <= self.filters.get("range4"):
				sales_order_data["advance"] = 0.0
				sales_order_data["outstanding"] = i.get("grand_total")
				sales_order_data["total_due"] = i.get("grand_total")
				sales_order_data["range1"] = sales_order_data["range2"] = sales_order_data["range3"] = 0.0
				sales_order_data["range4"] = i.get("grand_total")
				sales_order_data["range5"] = 0.0
			else:
				sales_order_data["advance"] = 0.0
				sales_order_data["outstanding"] = i.get("grand_total")
				sales_order_data["total_due"] = i.get("grand_total")
				sales_order_data["range1"] = sales_order_data["range2"] = sales_order_data["range3"] = sales_order_data["range4"] = 0.0
				sales_order_data["range5"] = i.get("grand_total")

			overall_outstanding += sales_order_data["outstanding"]
			overall_advance += sales_order_data["advance"]
			overall_total_due += sales_order_data["total_due"]
			overall_range1 += sales_order_data["range1"]
			overall_range2 += sales_order_data["range2"]
			overall_range3 += sales_order_data["range3"]
			overall_range4 += sales_order_data["range4"]
			overall_range5 += sales_order_data["range5"]

   
		self.data.append({"party": "Open Orders", "indent": 0, "advance": overall_advance, "outstanding": overall_outstanding, "total_due": overall_total_due, "range1": overall_range1, "range2": overall_range2, "range3": overall_range3, "range4": overall_range4, "range5": overall_range5})
  
		customer_data_dict = {}
		for i in doc:
			customer_name = i.get("customer")
			if customer_name not in customer_data_dict:
				customer_data_dict[customer_name] = {
					"party": customer_name,
					"territory": i.get("territory"),
					"customer_group": i.get("customer_group"),
					"currency": i.get("currency"),
					"indent": 1,
					"advance": 0.0,
					"outstanding": 0.0,
					"total_due": 0.0,
					"range1": 0.0,
					"range2": 0.0,
					"range3": 0.0,
					"range4": 0.0,
					"range5": 0.0
				}

			transaction_date = i.get("transaction_date") or today
			age = (today - transaction_date).days

			customer_data_dict[customer_name]["advance"] += i.get("advance_paid")
			customer_data_dict[customer_name]["outstanding"] += i.get("grand_total")
			customer_data_dict[customer_name]["total_due"] += i.get("grand_total")

			if age <= self.filters.get("range1"):
				customer_data_dict[customer_name]["range1"] += i.get("grand_total")
			elif age <= self.filters.get("range2"):
				customer_data_dict[customer_name]["range2"] += i.get("grand_total")
			elif age <= self.filters.get("range3"):
				customer_data_dict[customer_name]["range3"] += i.get("grand_total")
			elif age <= self.filters.get("range4"):
				customer_data_dict[customer_name]["range4"] += i.get("grand_total")
			else:
				customer_data_dict[customer_name]["range5"] += i.get("grand_total")

		self.data.extend(customer_data_dict.values())

		
   
	def get_party_total(self, args):
		self.party_total = frappe._dict()

		for d in self.receivables:
			self.init_party_total(d)

			# Add all amount columns
			for k in list(self.party_total[d.party]):
				if k not in ["currency", "sales_person"]:

					self.party_total[d.party][k] += d.get(k, 0.0)

			# set territory, customer_group, sales person etc
			self.set_party_details(d)

	def init_party_total(self, row):
		self.party_total.setdefault(
			row.party,
			frappe._dict(
				{
					"invoiced": 0.0,
					"paid": 0.0,
					"credit_note": 0.0,
					"outstanding": 0.0,
					"range1": 0.0,
					"range2": 0.0,
					"range3": 0.0,
					"range4": 0.0,
					"range5": 0.0,
					"total_due": 0.0,
					"future_amount": 0.0,
					"sales_person": [],
				}
			),
		)

	def set_party_details(self, row):
		self.party_total[row.party].currency = row.currency

		for key in ("territory", "customer_group", "supplier_group"):
			if row.get(key):
				self.party_total[row.party][key] = row.get(key)

		if row.sales_person:
			self.party_total[row.party].sales_person.append(row.sales_person)

		if self.filters.sales_partner:
			self.party_total[row.party]["default_sales_partner"] = row.get("default_sales_partner")

	def get_columns(self):
		self.columns = []
		self.add_column(
			label=_(self.party_type),
			fieldname="party",
			fieldtype="Link",
			options=self.party_type,
			width=180,
		)

		if self.party_naming_by == "Naming Series":
			self.add_column(_("{0} Name").format(self.party_type), fieldname="party_name", fieldtype="Data")

		credit_debit_label = "Credit Note" if self.party_type == "Customer" else "Debit Note"

		self.add_column(_("Advance Amount"), fieldname="advance")
		self.add_column(_("Invoiced Amount"), fieldname="invoiced")
		self.add_column(_("Paid Amount"), fieldname="paid")
		self.add_column(_(credit_debit_label), fieldname="credit_note")
		self.add_column(_("Outstanding Amount"), fieldname="outstanding")

		if self.filters.show_gl_balance:
			self.add_column(_("GL Balance"), fieldname="gl_balance")
			self.add_column(_("Difference"), fieldname="diff")

		self.setup_ageing_columns()

		if self.filters.show_future_payments:
			self.add_column(label=_("Future Payment Amount"), fieldname="future_amount")
			self.add_column(label=_("Remaining Balance"), fieldname="remaining_balance")

		if self.party_type == "Customer":
			self.add_column(
				label=_("Territory"), fieldname="territory", fieldtype="Link", options="Territory"
			)
			self.add_column(
				label=_("Customer Group"),
				fieldname="customer_group",
				fieldtype="Link",
				options="Customer Group",
			)
			if self.filters.show_sales_person:
				self.add_column(label=_("Sales Person"), fieldname="sales_person", fieldtype="Data")

			if self.filters.sales_partner:
				self.add_column(label=_("Sales Partner"), fieldname="default_sales_partner", fieldtype="Data")

		else:
			self.add_column(
				label=_("Supplier Group"),
				fieldname="supplier_group",
				fieldtype="Link",
				options="Supplier Group",
			)

		self.add_column(
			label=_("Currency"), fieldname="currency", fieldtype="Link", options="Currency", width=80
		)

	def setup_ageing_columns(self):
		for i, label in enumerate(
			[
				"0-{range1}".format(range1=self.filters["range1"]),
				"{range1}-{range2}".format(
					range1=cint(self.filters["range1"]) + 1, range2=self.filters["range2"]
				),
				"{range2}-{range3}".format(
					range2=cint(self.filters["range2"]) + 1, range3=self.filters["range3"]
				),
				"{range3}-{range4}".format(
					range3=cint(self.filters["range3"]) + 1, range4=self.filters["range4"]
				),
				"{range4}-{above}".format(range4=cint(self.filters["range4"]) + 1, above=_("Above")),
			]
		):
			self.add_column(label=label, fieldname="range" + str(i + 1))

		# Add column for total due amount
		self.add_column(label="Total Amount Due", fieldname="total_due")


def get_gl_balance(report_date):
	return frappe._dict(
		frappe.db.get_all(
			"GL Entry",
			fields=["party", "sum(debit -  credit)"],
			filters={"posting_date": ("<=", report_date), "is_cancelled": 0},
			group_by="party",
			as_list=1,
		)
	)
