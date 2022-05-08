from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class Invoice(models.Model):
	_inherit = 'account.move'

	# ns_origin_mrc = fields.Many2one('sale.subscription', 'Origin MRC', related="invoice_line_ids.subscription_id")
	ns_origin_mrc = fields.Many2one('sale.subscription', 'Origin MRC', compute="compute_origin_mrc")
	ns_billing_contact = fields.Many2one('res.partner', 'Billing Contact')
	ns_operation_site = fields.Many2one('operating.sites', 'Operation Site', related='ns_origin_mrc.x_studio_original_sales_order.x_studio_operation_site')

	@api.depends('invoice_line_ids')
	def compute_origin_mrc(self):
		for rec in self:
			rec.ns_origin_mrc = []
			# sale_order = self.env['sale.subscription'].search([('invoice_line_ids.subscription_id.id','=',self.ns_origin_mrc)], limit=1)
			subs_ids = self.invoice_line_ids
			for item in subs_ids:
				if item.subscription_id:
					rec.ns_origin_mrc = item.subscription_id.id
					break