from odoo import api, models, api, exceptions, _
import datetime
from dateutil.relativedelta import relativedelta

class StudentCard(models.AbstractModel):
	_name = 'report.nrs_de_01_invoice_statement.rep_invoice_statement'

	def _get_summary_current(self, operating_sites, product_categs, lines):
		summary_current = []
		current_charge = 0
		for operating in operating_sites:
			new_lines = lines.filtered(lambda l:l.x_operating_sites.id == operating.id)
			if new_lines:
				summary_operating = {'name': operating.name, 'detil': []}

				for categ in product_categs:
					new_lines_filtered = new_lines.filtered(lambda l:l.product_id.categ_id.id == categ.id)
					qty = 0
					subtotal = 0
					nrc= 0
					mrc = 0
					taxes = ''
					for li in new_lines_filtered:
						qty += li.quantity
						subtotal += li.price_total
						if li.product_id.x_studio_charge_type == 'Monthly':
							mrc += li.price_subtotal
						else:
							nrc += li.price_subtotal
						for tx in li.tax_ids:
							if not taxes:
								taxes += tx.description
							else:
								if tx.description not in taxes:
									taxes += ", " + tx.description
					summary_operating['detil'].append({
						'name': categ.name,
						'quantity': qty,
						'subtotal': subtotal,
						'nrc': nrc,
						'mrc': mrc,
						'taxes': taxes
					})
					current_charge += subtotal
				summary_current.append(summary_operating)
		return [current_charge, summary_current]

	def _get_payment_received(self, year, month, company, partner):
		last_month_start = datetime.date(year, month, 1) - relativedelta(months=1)
		last_month_end = last_month_start + relativedelta(months=1) - relativedelta(days=1)
		payments = self.env['account.payment'].search([('partner_type', '=', 'customer'), ('company_id', '=', company.id), ('partner_id', '=', partner.id), ('date', '>=', last_month_start), ('date', '<=', last_month_end), ('state', '=', 'posted')])
		payment_received = payments and sum([a.amount if a.payment_type == 'inbound' else -a.amount for a in payments]) or 0
		return payment_received

	def _check_allowed(self, docs):
		partner_id = []
		company_id = []
		invoice_date = []
		invoice_payment_term_id = []
		invoice_date_due = []
		ns_payment_instruction_id = []
		for d in docs:
			if d.partner_id.id not in partner_id: partner_id.append(d.partner_id.id)
			if d.company_id.id not in company_id: company_id.append(d.company_id.id)
			if d.invoice_payment_term_id.id not in invoice_payment_term_id: invoice_payment_term_id.append(d.invoice_payment_term_id.id)
			if d.ns_payment_instruction_id.id not in ns_payment_instruction_id: ns_payment_instruction_id.append(d.ns_payment_instruction_id.id)
			if d.invoice_date  not in invoice_date: invoice_date.append(d.invoice_date)
			if d.invoice_date_due not in invoice_date_due: invoice_date_due.append(d.invoice_date_due)
		if len(partner_id) > 1 or len(company_id) > 1 :
			raise exceptions.ValidationError(_("You have selected invoices from different companies. Please ensure you only select invoices from the same company account or subsidiaries"))
		if len(invoice_date) != 1:
			raise exceptions.ValidationError(_("You have selected invoices with different periods. Please select invoices within the same month."))	
		else:
			if not invoice_date[0]:
				raise exceptions.ValidationError(_("You have selected invoices with different periods. Please select invoices within the same month."))	
		if len(invoice_payment_term_id) > 1:
			raise exceptions.ValidationError(_("You have selected invoices with different payment terms. Please ensure you only select invoices with the same payment terms"))
		if len(ns_payment_instruction_id) > 1:
			raise exceptions.ValidationError(_("You have selected invoices with different payment instructions. Please select invoices with single uniformed payment instruction"))	
		return True

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['account.move'].browse(docids)
		month = list(set([a.month for a in docs.mapped('invoice_date') if a]))
		year = list(set([a.year for a in docs.mapped('invoice_date') if a]))

		self._check_allowed(docs)
		invoice_date_due = self.env['account.move']
		for ddue in  docs:
			if not invoice_date_due and ddue.invoice_date_due:
				invoice_date_due += ddue
				continue 
			if ddue.invoice_date_due and ddue.invoice_date_due not in invoice_date_due.mapped('invoice_date_due'):  
				invoice_date_due += ddue
		payment_instruction = docs.mapped('ns_payment_instruction_id')
		partner = docs.mapped('partner_id')
		first_doc = docs[0]
		doc = first_doc
		company = first_doc.company_id

		payment_received = self._get_payment_received(year[0], month[0], company, partner)

		lines = self.env['account.move.line'].search([('move_id', 'in', docs._ids), ('exclude_from_invoice_tab', '=', False)])
		operating_site = [a.x_operating_sites.id for a in lines if a.x_operating_sites]
		operating_sites = self.env['operating.sites'].search([('id', 'in', operating_site)], order='id')
		product_categs = self.env['product.category'].search([('id', '>', 0)], order='id')

		current_charge, summary_current = self._get_summary_current(operating_sites, product_categs, lines)
		adjustment = sum(docs.mapped('ns_adjustments'))
		late_payment = sum(docs.mapped('ns_late_interest'))
		summary = {
			'currency': first_doc.currency_id,
			'previous_charge': partner.total_overdue,
			'payment_received': payment_received,
			'balance_carried_forward': partner.total_overdue - payment_received,
			'late_payment': late_payment,
			'current_charge': current_charge,
			'adjustment': adjustment,
			'total_payment_due': (partner.total_overdue - payment_received) + late_payment + current_charge + adjustment,
		}

		so_origin = lines.mapped('x_origin')
		billing_contact = ""
		if len(so_origin) == 1:
			billing_contact = so_origin.x_studio_billing_contact_1.display_name
		data = {
			'partner': partner,
			'doc': doc,
			'company': company,
			'invoice_date_due': invoice_date_due,
			'summary': summary,
			'lines': lines,
			'doc_user': first_doc,
			'operating_site': operating_site,
			'product_categs': product_categs,
			'summary_current': summary_current,
			'billing_contact': billing_contact,
			'payment_instruction': payment_instruction,
		}
		return {
			'doc_ids': docids,
			'doc_model': 'account.move',
			'docs': docs,
			'doc': doc or first_doc,
			'data': data,
		}