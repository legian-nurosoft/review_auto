# -*- coding: utf-8 -*-

from odoo import models, api, _, _lt, fields

class MulticurrencyRevaluationReport(models.Model):
    _inherit = 'account.multicurrency.revaluation'

    @property
    def filter_show_usd_budget(self):
        return None

    @property
    def filter_show_usd_real(self):
        return None


    @property
    def filter_show_ifrs(self):
        return None

    @property
    def filter_show_gaap(self):
        return None


