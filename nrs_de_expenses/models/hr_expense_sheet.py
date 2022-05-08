from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.addons.hr_expense.models.hr_expense import HrExpenseSheet as HrExpenseSheetOrigin

class HrExpenseSheet(models.Model):
    """inherit hr expense sheer"""
    _inherit = 'hr.expense.sheet'
    
    def _track_subtype(self, init_values):
        """disable notification on change state of expense"""
        return super(HrExpenseSheetOrigin, self)._track_subtype(init_values)
    
HrExpenseSheetOrigin._track_subtype = HrExpenseSheet._track_subtype

