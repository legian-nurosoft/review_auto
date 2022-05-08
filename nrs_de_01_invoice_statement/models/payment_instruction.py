from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class PaymentInstruction(models.Model):
	_name = 'ns.payment.instruction'
	_description = 'Payment Instruction'
	_order = "ns_sequence asc, id asc"
	_rec_name = 'ns_name'

	ns_active = fields.Boolean("Active", default=True)
	ns_name = fields.Char("Payment Instruction")
	ns_sequence = fields.Integer("Sequence")
	ns_company_id = fields.Many2one("res.company", "DE Company")

	ns_account_holder = fields.Char("Account Holder", translate=True)
	ns_account_number = fields.Char("Account Number", translate=True)
	ns_bank_address = fields.Char("Bank Address", translate=True)
	ns_bank_address_2 = fields.Char("Bank Address 2", translate=True)

	ns_bank_name = fields.Char("Bank Name", translate=True)	
	ns_swift_code = fields.Char("SWIFT Code", translate=True)


