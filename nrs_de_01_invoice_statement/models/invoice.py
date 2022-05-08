from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class Invoice(models.Model):
	_inherit = 'account.move'

	ns_late_interest = fields.Monetary("Late Payment / Interest Charges", tracking=True)
	ns_adjustments = fields.Monetary("Adjustments", tracking=True)

	ns_payment_instruction_id = fields.Many2one("ns.payment.instruction", "Payment Instruction")

	ns_account_holder = fields.Char("Account Holder", related="ns_payment_instruction_id.ns_account_holder")
	ns_account_number = fields.Char("Address 1", related="ns_payment_instruction_id.ns_account_number")
	ns_bank_address = fields.Char("Address 2", related="ns_payment_instruction_id.ns_bank_address")

	ns_bank_name = fields.Char("Wire Instruction", related="ns_payment_instruction_id.ns_bank_name")
	ns_bank_address_2 = fields.Char("Address", related="ns_payment_instruction_id.ns_bank_address_2")
	ns_swift_code = fields.Char("Routing Code", related="ns_payment_instruction_id.ns_swift_code")

	
	def open_adjustment_popup(self):
		self.ensure_one()
		adjustment_id = self.env['ns.move.adjustment'].create({'ns_move_id': self.id})
		return {
			'name': 'Adjustment',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ns.move.adjustment',
			'target': 'new',
			'res_id': adjustment_id.id,
		}

class InvoiceLine(models.Model):
	_inherit = 'account.move.line'

	ns_is_adjustment = fields.Boolean(default=False)
	price_unit = fields.Monetary(currency_field='currency_id')

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	price_unit = fields.Monetary(currency_field='currency_id')


class MoveAdjustment(models.TransientModel):
	_name = 'ns.move.adjustment'

	ns_type = fields.Selection([
			('adjustment', 'Adjustment'),
			('late_payment_charge','Late Payment Charge')
		], string='Type', default='adjustment')
	ns_remark = fields.Char('Remark')
	ns_currency_id = fields.Many2one('res.currency',string='Currency')
	ns_amount = fields.Monetary(string='Amount', currency_field='ns_currency_id')
	ns_company_id = fields.Many2one(related='ns_move_id.company_id', string='Company')
	ns_account_id = fields.Many2one('account.account', string='Account')
	ns_move_id = fields.Many2one('account.move', 'Move')

	def process(self):
		if not self.ns_move_id.partner_id.property_account_receivable_id:
			raise exceptions.ValidationError(_('Please configure the account receivable'))

		if self.ns_type == 'adjustment':
			self.ns_move_id.write({
					'ns_adjustments': self.ns_move_id.ns_adjustments + (self.ns_amount / self.ns_currency_id.rate)
				})
		else:
			self.ns_move_id.write({
					'ns_late_interest': self.ns_move_id.ns_late_interest + (self.ns_amount / self.ns_currency_id.rate)
				})

		value = abs(self.ns_amount / self.ns_currency_id.rate)
		self.ns_move_id.write({
			'line_ids': [
				[0,0,{
					'name': self.ns_remark,
					'account_id': self.ns_move_id.partner_id.property_account_receivable_id.id,
					'price_unit': value,
					'debit': value if self.ns_amount > 0 else 0,
					'credit': value if self.ns_amount < 0 else 0,
					'price_subtotal': value,
					'price_total': value,
					'currency_id': self.ns_currency_id.id,
					'exclude_from_invoice_tab': True,
					'ns_is_adjustment': True
				}],
				[0,0,{
					'name': self.ns_remark,
					'account_id': self.ns_account_id.id,
					'price_unit': value,
					'credit': value if self.ns_amount > 0 else 0,
					'debit': value if self.ns_amount < 0 else 0,
					'price_subtotal': value,
					'price_total': value,
					'currency_id': self.ns_currency_id.id,
					'exclude_from_invoice_tab': False,
					'ns_is_adjustment': True
				}]
			]
		})

