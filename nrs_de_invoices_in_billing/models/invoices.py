# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import AccessDenied

class InvoiceInBilling(models.Model):
    _inherit = 'account.move'

    # def action_confirm(self):
    #     if not (self.env.user.has_group('account.group_account_user') or self.env.user.has_group('account.group_account_invoice')):
    #         raise AccessDenied("You don't have access to use this page!")
    #     else:
    #         res = super(InvoiceInBilling, self).action_confirm()
    #         return res