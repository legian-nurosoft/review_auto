from odoo import models, fields, api, exceptions,_
from odoo.addons.hr_expense.models.account_move import AccountMove as AccountMoveInherit


class AccountMove(models.Model):
    """inherit account move"""
    _inherit = 'account.move'
    
    def button_cancel(self):
        """inherit inheritted button cancel and add context condition"""
        context = self.env.context
        for l in self.line_ids:
            if l.expense_id and 'from_refuse_sheet' not in context:
                l.expense_id.refuse_expense(reason=_("Payment Cancelled"))
        return super(AccountMoveInherit, self).button_cancel()
    
AccountMoveInherit.button_cancel = AccountMove.button_cancel