# -*- coding: utf-8 -*-
from odoo import api, models, api, exceptions, fields, _

class SalesOrder(models.Model):
	_inherit = 'sale.order'

	ns_can_edit = fields.Boolean(compute='_compute_can_edit_so')

	def _compute_can_edit_so(self):
		for rec in self:
			value = False
			if rec.user_id.id == self.env.user.id:
				value = True
			
			if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
				sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
				for team in sale_team:
					if rec.user_id.id in team.member_ids.ids:
						value = True

			if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
				sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
				for team in sale_team:
					if rec.user_id.id in team.member_ids.ids:
						value = True

			if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') \
					or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager') \
					or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_ops'):
				user = self.env.user
				if rec.company_id.id in user.company_ids.ids:
					value = True

			if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support') and rec.company_id.id == self.env.user.company_id.id:
				value = True

			rec.ns_can_edit = value	