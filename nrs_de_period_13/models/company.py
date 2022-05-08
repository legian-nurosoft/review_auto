from odoo import api, models, api, exceptions, fields, _
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    ns_period_lock_date_all_users = fields.Date(string="Lock Date for 12 Periods for All Users")

    def _get_user_fiscal_lock_date(self):
        """Get the fiscal lock date for this company depending on the user"""
        self.ensure_one()
        lock_date = max(self.period_lock_date or date.min, self.ns_period_lock_date_all_users or date.min, self.fiscalyear_lock_date or date.min)
        if self.user_has_groups('account.group_account_manager'):
            lock_date = max(self.ns_period_lock_date_all_users or date.min, self.fiscalyear_lock_date or date.min)
        return lock_date

    def _get_user_fiscal_lock_date_period_13(self):
        self.ensure_one()
        lock_date = self.fiscalyear_lock_date or date.min
        return lock_date