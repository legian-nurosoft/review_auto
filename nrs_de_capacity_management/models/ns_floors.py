from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class XFloor(models.Model):
	_name = 'ns.ns_floors'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Floors'
	_order = "ns_sequence asc, id asc"
	_rec_name = 'ns_name'

	active = fields.Boolean("Active", default=True)
	ns_name = fields.Char("Name")
	ns_sequence = fields.Integer("Sequence")
	ns_operation_site = fields.Many2one("operating.sites", "Operation Site")
	company_id = fields.Many2one('res.company')
