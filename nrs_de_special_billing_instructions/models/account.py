from odoo import api, models, api, exceptions, fields, _


class Invoice(models.Model):
    _inherit = 'account.move'

    ns_special_billing_instruction = fields.Boolean(string="Special Billing Instructions", default=False, readonly=True)
    ns_special_billing_instruction_ids = fields.One2many('ns.special.billing.instruction.invoice', 'ns_move_id', string='Special Billing Instruction Lines', default=False, readonly=True)
