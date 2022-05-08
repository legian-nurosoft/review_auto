# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"
        
    @property
    def filter_show_period_13(self):
        return False

    @property
    def filter_show_period_13_only(self):
        return False
     

        
   

    