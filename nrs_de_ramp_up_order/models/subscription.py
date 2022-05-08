from odoo import fields, models, api, exceptions, _
import calendar
from datetime import timedelta, datetime
from odoo.exceptions import UserError
from odoo.tools import format_date, float_compare
from odoo.tools.float_utils import float_is_zero
from dateutil.relativedelta import relativedelta


INTERVAL_FACTOR = {
	'daily': 30.0,
	'weekly': 30.0 / 7.0,
	'monthly': 1.0,
	'yearly': 1.0 / 12.0,
}

PERIODS = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}

class MRC(models.Model):
	_inherit = 'sale.subscription'

	ns_ramp_up = fields.Many2one('ns.ramp.ups', 'Ramp Up')
	subscription_log_ids = fields.One2many('sale.subscription.log', 'subscription_id', string='Subscription Logs', readonly=True, domain=[('ns_is_nrc', '=', False)])
	ns_nrc_log_ids = fields.One2many('sale.subscription.log', 'subscription_id', string='NRCs Logs', readonly=True, domain=[('ns_is_nrc', '=', True)])

	recurring_invoice_line_ids = fields.One2many('sale.subscription.line', 'analytic_account_id', string='Subscription Lines', copy=True, domain=[('ns_is_nrc', '=', False)])
	ns_nrc_line_ids = fields.One2many('sale.subscription.line', 'analytic_account_id', string='NRC Lines', copy=True, domain=[('ns_is_nrc', '=', True)], tracking=40)
	ns_non_recurring_total = fields.Float(compute='_ns_amount_all', string="Non Recurring Price", store=True, tracking=40)

	@api.depends('ns_nrc_line_ids', 'ns_nrc_line_ids.price_subtotal')
	def _ns_amount_all(self):
		"""
		Compute the total amounts of the subscription.
		"""
		for subscription in self:
			amount_tax = 0.0
			recurring_total = 0.0
			for line in subscription.ns_nrc_line_ids:
				recurring_total += line.price_subtotal
				# _amount_line_tax needs singleton
				amount_tax += line._amount_line_tax()
			# non_recurring = subscription.currency_id and subscription.currency_id.round(recurring_total) or 0.0
			subscription.update({
				'ns_non_recurring_total': recurring_total,
			})

	def _message_track(self, tracked_fields, initial):
		res = super()._message_track(tracked_fields, initial)
		updated_fields, commands = res
		if any(f in updated_fields for f in ['ns_non_recurring_total', 'ns_nrc_line_ids']):
			# Intial may not always contains all the needed values if they didn't changed
			# Fallback on record value in that case
			initial_rrule_type = INTERVAL_FACTOR[initial.get('recurring_rule_type', self.recurring_rule_type)]
			initial_rrule_interval = initial.get('recurring_interval', self.recurring_interval)
			old_factor = initial_rrule_type / initial_rrule_interval
			old_value_monthly = initial.get('ns_non_recurring_total', self.ns_non_recurring_total) * old_factor
			new_factor = INTERVAL_FACTOR[self.recurring_rule_type] / self.recurring_interval
			new_value_monthly = self.ns_non_recurring_total * new_factor
			delta = new_value_monthly - old_value_monthly
			cur_round = self.company_id.currency_id.rounding
			if not float_is_zero(delta, precision_rounding=cur_round):
				self.env['sale.subscription.log'].sudo().create({
					'event_date': fields.Date.context_today(self),
					'subscription_id': self.id,
					'currency_id': self.currency_id.id,
					'recurring_monthly': new_value_monthly,
					'amount_signed': delta,
					'event_type': '1_change',
					'category': self.stage_id.category,
					'user_id': self.user_id.id,
					'team_id': self.team_id.id,
					'ns_is_nrc': True,
				})
		if 'stage_id' in updated_fields:
			old_stage_id = initial['stage_id']
			new_stage_id = self.stage_id
			if new_stage_id.category in ['progress', 'closed'] and old_stage_id.category != new_stage_id.category:
				# subscription started or churned
				start_churn = {'progress': {'type': '0_creation', 'amount_signed': self.ns_non_recurring_total,
											'recurring_monthly': self.ns_non_recurring_total},
								'closed': {'type': '2_churn', 'amount_signed': -self.ns_non_recurring_total,
											'recurring_monthly': 0}}
				self.env['sale.subscription.log'].sudo().create({
					'event_date': fields.Date.context_today(self),
					'subscription_id': self.id,
					'currency_id': self.currency_id.id,
					'recurring_monthly': start_churn[new_stage_id.category]['recurring_monthly'],
					'amount_signed': start_churn[new_stage_id.category]['amount_signed'],
					'event_type': start_churn[new_stage_id.category]['type'],
					'category': self.stage_id.category,
					'user_id': self.user_id.id,
					'team_id': self.team_id.id,
					'ns_is_nrc': True,
				})
		return res

	def _prepare_invoice_lines(self, fiscal_position):
		res = super(MRC, self)._prepare_invoice_lines(fiscal_position)
		mrc_lines = []
		nrc_lines = []
		new_res = []
		sequence = 0

		for line in res:
			product = self.env['product.product'].browse(line[2]['product_id'])
			if product.recurring_invoice:
				mrc_lines.append(line)
			else:
				line[2]['subscription_start_date'] = False
				line[2]['subscription_end_date'] = False
				nrc_lines.append(line)
		
		if len(nrc_lines) != 0:
			new_res.append(
				{
					'sequence': sequence,
					'name': 'Non Recurring Charge (NRC)',
					'subscription_id': False,
					'price_unit': False,
					'discount': False,
					'quantity': False,
					'product_uom_id': False,
					'product_id': False,
					'tax_ids': False,
					'analytic_account_id': False,
					'analytic_tag_ids': False,
					'subscription_start_date': False,
					'subscription_end_date': False,
					'display_type': 'line_section'
				}
			)
			sequence += 1
			
			for line in nrc_lines:
				line[2]['sequence'] = sequence
				new_res.append(line)
				sequence += 1

		if len(mrc_lines) != 0:
			new_res.append(
				{	
					'sequence': sequence,
					'name': 'Monthly Recurring Charge (MRC)',
					'subscription_id': False,
					'price_unit': False,
					'discount': False,
					'quantity': False,
					'product_uom_id': False,
					'product_id': False,
					'tax_ids': False,
					'analytic_account_id': False,
					'analytic_tag_ids': False,
					'subscription_start_date': False,
					'subscription_end_date': False,
					'display_type': 'line_section'
				}
			)
			sequence += 1

			for line in mrc_lines:
				line[2]['sequence'] = sequence
				new_res.append(line)
				sequence += 1

		return new_res
	
	def write(self, vals):
		res = super(MRC, self).write(vals)
		if self.ns_nrc_line_ids:
			last = self.ns_nrc_line_ids[len(self.ns_nrc_line_ids)-1]
		return res

			
class SaleSubscriptionLine(models.Model):
	_inherit = "sale.subscription.line"

	ns_is_nrc = fields.Boolean('Is NRC', default=False)
	ns_invoiced = fields.Float('Invoiced', compute="get_invoiced")

	def get_invoiced(self):
		for rec in self:
			if rec.ns_is_nrc:
				invoice_line = self.env['account.move.line'].search([('ns_nrc_line', '=', rec.id)])
				rec.ns_invoiced = sum(invoice_line.mapped('quantity')) 
			else:
				rec.ns_invoiced = 0

	@api.model
	def create(self, values):
		if not self.env['product.product'].browse(values['product_id']).recurring_invoice:
			values['ns_is_nrc'] = True

		return super(SaleSubscriptionLine, self).create(values)
		

class SaleSubscriptionLog(models.Model):
	_inherit = 'sale.subscription.log'

	ns_is_nrc = fields.Boolean('Is NRC', default=False)
	event_type = fields.Selection(
		string='Type of event',
		selection=[('0_creation', 'Creation'), ('1_change', 'Change'), ('2_churn', 'Churn')],
		required=True, readonly=True,)


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	ns_nrc_line = fields.Many2one('sale.subscription.line', 'NRC Lines from MRC')
