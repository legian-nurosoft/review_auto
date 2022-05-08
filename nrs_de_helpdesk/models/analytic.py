# -*- coding: utf-8 -*-

from odoo import models, api, fields, exceptions, _

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    ns_minutes = fields.Integer(string='Duration (Minutes)', default=0)

    @api.onchange('unit_amount')
    def unit_amount_changed(self):        
        self.ns_minutes = self.unit_amount * 60

    @api.onchange('ns_minutes')
    def ns_minutes_changed(self):
        mod = self.ns_minutes % 15
        if mod > 0:
            self.ns_minutes += 15 - mod
        
        self.unit_amount = self.ns_minutes / 60

