# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class CrmFxRate(models.Model):
    _name = 'crm.fx.rate'
    _description = 'CRM FX RATE'
    _rec_name = 'currency_id'
    _order = "date_start desc"

    currency_id = fields.Many2one('res.currency', 'Currency', help="Choose a currency different than USD.", required=True)
    rate = fields.Float(string="Rate against USD", default=1.0, help="Set the currency amount that makes 1 USD in the selected time frame.", required=True)
    date_start = fields.Date('Start date', required=True)
    date_end = fields.Date('End date', required=True)

    @api.onchange('date_start')
    def get_end_date(self):
        if self.date_start:
            self.date_end = self.date_start + relativedelta(years=1, days=-1)

    def update_old_leads(self):
        """
            After adding new quarter rate, old quarter leads need to update as per latest rate
        """
        old_leads = self.env['crm.lead'].search([('won_status', 'not in', ['won', 'lost'])])
        return old_leads.sudo()._compute_mrc_nrc()


    def update_old_orders(self):
        for rec in self:
            orders = self.env['sale.order'].sudo().search([('x_studio_crm_fx_rate','=',rec.id), ('date_order','>=',rec.date_start), ('date_order','<=',rec.date_end)])
            for order in orders:
                order.x_studio_total_usd = order.amount_total / rec.rate

    def update_old_journal_items(self):
        for rec in self:
            move_lines = self.env['account.move.line'].sudo().search([('currency_id','=',rec.currency_id.id), ('date','>=',rec.date_start), ('date','<=',rec.date_end)])
            for m_line in move_lines:
                m_line._compute_usd_budget_amount()
                    
