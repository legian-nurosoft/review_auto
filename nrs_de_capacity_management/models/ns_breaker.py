from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class XBreaker(models.Model):
	_name = 'ns.ns_breaker'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Breaker'
	_order = "ns_sequence asc, id asc"
	_rec_name = 'ns_name'

	active = fields.Boolean("Active", default=True)
	ns_name = fields.Char("Name")
	ns_pdu = fields.Many2one('ns.ns_pdu', 'PDU')
	ns_sequence = fields.Integer("Sequence")
	ns_customer = fields.Many2one('res.partner', 'Customer')
	ns_sold = fields.Boolean("Sold")
	ns_reserved = fields.Boolean("Reserved")
	ns_reserve_date_until = fields.Date("Reserved Until")
	ns_sale_order_line_id = fields.Many2one('sale.order.line','Reserved by')
	ns_stage = fields.Selection(
		[
			('available', 'Available'),
			('installed', 'Installed'),
			('assigned', 'Assigned'),
			('sold', 'Sold'),
			('reserved', 'Reserved'),
			('rofr', 'ROFR'),
			('blocked', 'Blocked'),
			('pending_available', 'Pending Available'),
		], string='Stage', default='available', track_visibility='onchange', tracking=True, group_expand='_group_expand_states')
	company_id = fields.Many2one('res.company')

	def _group_expand_states(self, states, domain, order):
		return [key for key, val in type(self).ns_stage.selection]
