from odoo import fields, models, api, exceptions, _
import calendar
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
	_inherit = "sale.order"

	# def action_submit_quotation(self):
	# 	check = self.env['ns.sale.permission.config'].check_rule(self.x_studio_total_usd, self.order_line)
	# 	if not check:
	# 		raise ValidationError(_('Cannot Approve quotation to sale order'))
	# 	return super(SaleOrder, self).action_submit_quotation()
	ns_can_approve = fields.Boolean(compute="get_allow_to_approval")
	x_studio_total_usd = fields.Float("Total (USD)", compute="get_total_usd", store=True)

	@api.depends('amount_total','currency_id')
	def get_total_usd(self):
		fx_rate = self.env['crm.fx.rate']
		for rec in self:
			current_date = str(fields.Date.context_today(self))
			current_rate = fx_rate.search([('date_start', '<=', current_date), ('currency_id', '=', rec.currency_id.id), ('date_end', '>=', current_date)], order='date_start desc', limit=1)
			if current_rate:
				rec.update({
				        'x_studio_total_usd': rec.amount_total / current_rate.rate,
				    })

	def get_allow_to_approval(self):
		check = self.env['ns.sale.permission.config'].check_rule(self.x_studio_total_usd, self.order_line)
		print("check", check)
		for rec in self:
			rec.ns_can_approve = check
		
	def action_approve_quotation(self):
		check = self.env['ns.sale.permission.config'].check_rule(self.x_studio_total_usd, self.order_line)
		if not check:
			raise ValidationError(_('Cannot Approve quotation to sale order'))
		return super().action_approve_quotation()



#request by Janet to Translation field Name
class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	name = fields.Text(string='Description', required=True, translate=True)

class ResCurrency(models.Model):
	_inherit = "res.currency"

	name = fields.Char(string='Currency', size=3, required=True, translate=True, help="Currency Code (ISO 4217)")