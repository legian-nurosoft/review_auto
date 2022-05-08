from odoo import fields, models, api, exceptions, _
import calendar
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError

SELECTION = [
	("=", "is equal to"),
	(">", "greater than"),
	("<", "less than"),
	(">=", "greater than or equal to"),
	("<=", "less than or equal to"),
	("between", "between"),
	]


class ConfigSalePermission(models.Model):
	_name = 'ns.sale.permission.config'

	@api.model 
	def get_default_cur(self):
		return self.env.ref("base.USD").id

	@api.model 
	def get_default_categ(self):
		return self.env.ref("base.module_category_sales_sales").id

	name = fields.Many2one('res.groups', "Group Name")
	ns_application_id = fields.Many2one("ir.module.category", "Application", default=get_default_categ)
	ns_currency_id = fields.Many2one("res.currency", "Currency", default=get_default_cur)
	ns_operation_usd = fields.Selection(selection=SELECTION, default="=")
	ns_total_usd = fields.Monetary("Total (USD)", currency_field ="ns_currency_id")
	ns_total_usd_max = fields.Monetary("Total (USD) Max", currency_field ="ns_currency_id")
	ns_operation_percent = fields.Selection(selection=SELECTION, default="=")
	ns_disc_percent = fields.Float("Disc.%")
	ns_disc_percent_max = fields.Float("Disc.% Max")


	@api.constrains('name')
	def _check_group_name(self):
		for record in self:
			other = self.search([('name', '=', record.name.id), ('id', '!=', record.id)])
			if other:
				raise ValidationError("The Group Name must be unique")
		# all records passed the test, don't return anything

	def _check_rule_usd(self, usd):
		res = False
		if self.ns_operation_usd == '=':
			res = usd == self.ns_total_usd
		elif self.ns_operation_usd == '>':
			res = usd > self.ns_total_usd
		elif self.ns_operation_usd == '<':
			res = usd < self.ns_total_usd
		elif self.ns_operation_usd == '>=':
			res = usd >= self.ns_total_usd
		elif self.ns_operation_usd == '<=':
			res = usd <= self.ns_total_usd
		elif self.ns_operation_usd == 'between':
			res = self.ns_total_usd <= usd <= self.ns_total_usd_max
		return res

	def _check_rule_percent(self, lines):
		res = True
		for line in lines:
			percent = line.discount
			if percent == 0:
				continue
			if self.ns_operation_percent == '=':
				res = res and percent == self.ns_disc_percent
			elif self.ns_operation_percent == '>':
				res = res and percent > self.ns_disc_percent
			elif self.ns_operation_percent == '<':
				res = res and percent < self.ns_disc_percent
			elif self.ns_operation_percent == '>=':
				res = res and percent >= self.ns_disc_percent
			elif self.ns_operation_percent == '<=':
				res = res and percent <= self.ns_disc_percent
			elif self.ns_operation_percent == 'between':
				res = res and self.ns_disc_percent <= percent <= self.ns_disc_percent_max
		return res

	@api.model
	def check_rule(self, usd, lines):
		group = self.env['res.groups']
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_deal_desk"):
			group = self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_deal_desk")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_reg_manager"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_reg_manager")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_cont_manager"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_cont_manager")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_manager"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_manager")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_rep"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_rep")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_ops"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_ops")
		if self.env.user.has_group("nrs_de_permission_sales_team.nrs_group_sale_support"):
			group += self.env.ref("nrs_de_permission_sales_team.nrs_group_sale_support")
		if not group:
			return False
		res = False
		for gr in group:
			this = self.search([('name', '=', gr.id)])
			if not this:
				continue
			res = res or (this._check_rule_usd(usd) and this._check_rule_percent(lines))
		return res
