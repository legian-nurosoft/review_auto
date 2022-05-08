from odoo import api, models, api, exceptions, fields, _
import logging
import re
from odoo.osv import expression
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
import logging
from odoo.tools.misc import format_date
logger = logging.getLogger(__name__)


class AccountPeriod(models.Model):
    _inherit = 'account.move'
    nrs_period_13 = fields.Boolean('Period 13')

    @api.onchange('nrs_period_13')
    def set_values(self):
        if self.nrs_period_13 == False:
            self.line_ids.nrs_period = False
        if self.nrs_period_13 == True:
            self.line_ids.nrs_period = True

    def _check_fiscalyear_lock_date(self):
        for move in self:
            lock_date = move.company_id._get_user_fiscal_lock_date_period_13() if move.nrs_period_13 else move.company_id._get_user_fiscal_lock_date()
            period_13_message = ' period 13' if move.nrs_period_13 else ''
            if move.date <= lock_date:
                if self.user_has_groups('account.group_account_manager'):
                    message = _("You cannot add/modify%s entries prior to and inclusive of the lock date %s." % (period_13_message,format_date(self.env, lock_date)))
                else:
                    message = _("You cannot add/modify%s entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role" % (period_13_message, format_date(self.env, lock_date)))
                raise UserError(message)
        return True

class AccountPeriod(models.Model):
	_inherit = 'account.move.line'

	nrs_period = fields.Boolean('P13', default=False)

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_show_period_13_only = None
    filter_show_period_13 = None

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountReport, self)._get_options_domain(options)

        period_13_domain = []
        if options.get('show_period_13') == True and options.get('show_period_13_only') == True:
            raise AccessDenied('Can not choose both include period 13 and show period 13 only')

        if options.get('show_period_13') == False and options.get('show_period_13_only') == False   :
            # logger.info('value check %s' % check)
            period_13_domain = expression.OR([period_13_domain, [('nrs_period','=',False)]])
        
        if options.get('show_period_13_only') == True and options.get('show_period_13') == False :
            # logger.info('value check %s' % check)
            period_13_domain = expression.OR([period_13_domain, [('nrs_period','=',True)]])


        if len(period_13_domain) > 0:
            domain = expression.AND([domain, period_13_domain])

        return domain

 
class FinancialPeriod(models.Model):
    _inherit = "account.financial.html.report"    
    
    @property
    def filter_show_period_13(self):
        if self.nrs_period_13 and (self.id == 2 or self.id == 1) :
            return False
        else:
            return None
    @property
    def filter_show_period_13_only(self):
        if self.nrs_period_13 and (self.id == 2 or self.id == 1) :
            return False
        else:
            return None
        
    nrs_period_13 = fields.Boolean('Include Period 13 Entries', default=False)
