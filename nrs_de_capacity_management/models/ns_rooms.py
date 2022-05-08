from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class XRooms(models.Model):
	_name = 'ns.ns_rooms'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Rooms'
	_order = "ns_sequence asc, id asc"
	_rec_name = 'ns_name'

	active = fields.Boolean("Active", default=True)
	ns_name = fields.Char("Name")
	ns_sequence = fields.Integer("Sequence")
	ns_floor = fields.Many2one("ns.ns_floors", "Floor")
	ns_remarks = fields.Char("Remarks", translate=True)
	ns_room_description = fields.Char("Room Description", translate=True)
	ns_room_type = fields.Selection([('Space', 'Space'), ('Power', 'Power'), ('Auxiliary', 'Auxiliary')], "Room Type")
	ns_sequence = fields.Integer("Sequence")
	ns_ns_room__ns_space_count = fields.Integer("Room Count", compute="_get_room_space_count")
	company_id = fields.Many2one('res.company')


	def _get_room_space_count(self):
		results = self.env['ns.ns_space'].read_group([('ns_room', 'in', self.ids)], ['ns_room'], ['ns_room'])
		dic = {}
		for x in results: dic[x['ns_room'][0]] = x['ns_room_count']
		for record in self: record['ns_ns_room__ns_space_count'] = dic.get(record.id, 0)
