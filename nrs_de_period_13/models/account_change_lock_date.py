from odoo import api, models, api, exceptions, fields
from odoo.exceptions import AccessDenied, UserError
import logging
import re

class AccountPeriodLockDate(models.TransientModel):
    _inherit="account.change.lock.date"

    ns_period_lock_date_all_users = fields.Date(string="Lock Date for 12 Periods for All Users", default=lambda self: self.env.company.ns_period_lock_date_all_users)

    def change_lock_date(self):
        if self.user_has_groups('nrs_de_period_13.group_ns_account_administrator'):
            self.env.company.sudo().write({
                'period_lock_date': self.period_lock_date,
                'fiscalyear_lock_date': self.fiscalyear_lock_date,
                'tax_lock_date': self.tax_lock_date,
                'ns_period_lock_date_all_users': self.ns_period_lock_date_all_users
            })
        else:
            raise UserError(_('Only Accounting Administrators are allowed to change lock dates!'))
        return {'type': 'ir.actions.act_window_close'}

class CRMFXRateOldJournal(models.Model):
    _inherit="crm.fx.rate"

    def update_old_journal_items(self):
        if not self.env.user.has_group('nrs_de_period_13.group_ns_account_administrator'):
            raise AccessDenied("You don't have access to Update Old Journal Items")
        else:
            res = super(CRMFXRateOldJournal, self).update_old_journal_items()
            return res
