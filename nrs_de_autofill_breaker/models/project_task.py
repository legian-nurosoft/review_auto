from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class ProjectTask(models.Model):
	_inherit = 'project.task'

	x_studio_space_id = fields.Many2one("ns.ns_space", "Space ID", domain=[('ns_sold', '=', False)])
	x_studio_breaker_id = fields.Many2one("ns.ns_breaker", "Breaker ID", domain=[('ns_sold', '=', False)])


	@api.onchange('x_studio_space_id')
	def x_studio_space_id_change(self):
		if self.x_studio_space_id:
			self.x_studio_breaker_id = False

	@api.onchange('x_studio_breaker_id')
	def x_studio_breaker_id_change(self):
		if self.x_studio_breaker_id:
			self.x_studio_space_id = False

	@api.model 
	def create(self, vals):
		res = super(ProjectTask, self).create(vals)
		if vals.get('x_studio_space_id', 0):
			space = self.env['ns.ns_space'].browse(vals.get('x_studio_space_id', 0))
			space.write({'ns_sold': True, 'ns_customer': res.partner_id and res.partner_id.id or 0})
		if vals.get('x_studio_breaker_id', 0):
			space = self.env['ns.ns_breaker'].browse(vals.get('x_studio_breaker_id', 0))
			space.write({'ns_sold': True, 'ns_customer': res.partner_id and res.partner_id.id or 0})
		return res


	def write(self, vals):
		x_studio_space_id = vals.get('x_studio_space_id', 0)
		x_studio_breaker_id = vals.get('x_studio_breaker_id', 0)
		if 'x_studio_space_id' in vals or 'x_studio_breaker_id' in vals:
			for rec in self:
				if 'x_studio_space_id' in vals:
					space = self.env['ns.ns_space'].browse(rec.x_studio_space_id.id)
					if space:
						space.write({'ns_sold': False, 'ns_customer': False})
				if 'x_studio_breaker_id' in vals:
					breaker = self.env['ns.ns_breaker'].browse(rec.x_studio_breaker_id.id)
					if breaker:
						breaker.write({'ns_sold': False, 'ns_customer': False})
		res = super(ProjectTask, self).write(vals)
		if x_studio_space_id or x_studio_breaker_id:
			for rec in self:
				if x_studio_space_id:
					space = self.env['ns.ns_space'].browse(x_studio_space_id)
					space.write({'ns_sold': True, 'ns_customer': rec.partner_id and rec.partner_id.id or 0})
				if x_studio_breaker_id:
					space = self.env['ns.ns_breaker'].browse(x_studio_breaker_id)
					space.write({'ns_sold': True, 'ns_customer': rec.partner_id and rec.partner_id.id or 0})
		return res
