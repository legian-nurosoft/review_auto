# -*- coding: utf-8 -*-

from odoo import api, models
from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    ns_expense_required_tax = fields.Boolean('Required Expense Tax', help="Determine if tax input in Expense would be required for this company.")