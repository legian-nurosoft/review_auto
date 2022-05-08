from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class XSpace(models.Model):
	_name = 'ns.ns_space'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Space'
	_order = "ns_sequence asc, id asc"
	_rec_name = 'ns_name'
	
	active = fields.Boolean("Active", default=True)
	ns_name = fields.Char("Name")
	ns_customer = fields.Many2one('res.partner', 'Customer')
	ns_number_of_cabe = fields.Integer("Number of Cabe")
	ns_number_of_racks = fields.Integer("Number of Racks")
	ns_number_of_used_racks = fields.Integer("Number of Used Racks")
	ns_operation_site = fields.Many2one("operating.sites", "Operation Site")
	ns_racks_usage_rate = fields.Float("Racks Usage Rate", compute="_get_usage_rate", store=True)
	ns_room = fields.Many2one("ns.ns_rooms", 'Room')
	ns_sequence = fields.Integer("Sequence")
	ns_sold = fields.Boolean("Sold")
	ns_reserved = fields.Boolean("Reserved")
	ns_space_type = fields.Selection([('Cabinet', 'Cabinet'), ('Cage', 'Cage'), ('Hall', 'Hall')], "Space Type")
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
	ns_reserve_date_until = fields.Date("Reserved Until")
	ns_sale_order_line_id = fields.Many2one('sale.order.line','Reserved by')
	company_id = fields.Many2one('res.company')

	@api.depends("ns_number_of_used_racks","ns_number_of_racks")
	def _get_usage_rate(self):
		for record in self:
			if record.ns_number_of_racks != 0:
				record[('ns_racks_usage_rate')] = record.ns_number_of_used_racks / record.ns_number_of_racks

	def _group_expand_states(self, states, domain, order):
		return [key for key, val in type(self).ns_stage.selection]
