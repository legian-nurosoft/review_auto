# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMoveInherit(models.Model):    
    _inherit = 'account.move'

    ns_is_usd_currency = fields.Boolean('Is USD Currency', compute='_compute_is_usd_currency')

    @api.depends('currency_id')
    def _compute_is_usd_currency(self):
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        for rec in self:
            rec.ns_is_usd_currency = False            
            if usd_currency:
                if rec.currency_id.id == usd_currency.id:
                    rec.ns_is_usd_currency = True   


class AccountMoveLineInherit(models.Model):    
    _inherit = 'account.move.line'

    @api.model
    def _get_usd_currency(self):
        return self.env['res.currency'].search([('name','=','USD')],limit=1)


    ns_usd_currency_id = fields.Many2one('res.currency', default=_get_usd_currency)

    ns_debit_usd_budget = fields.Monetary(string='Debit USD (Budget)', default=0.0, currency_field='ns_usd_currency_id', store=True, compute='_compute_usd_budget_amount')
    ns_credit_usd_budget = fields.Monetary(string='Credit USD (Budget)', default=0.0, currency_field='ns_usd_currency_id', store=True, compute='_compute_usd_budget_amount')

    ns_debit_usd_real = fields.Monetary(string='Debit USD (Real)', default=0.0, currency_field='ns_usd_currency_id', store=True, compute='_compute_usd_real_amount')
    ns_credit_usd_real = fields.Monetary(string='Credit USD (Real)', default=0.0, currency_field='ns_usd_currency_id', store=True, compute='_compute_usd_real_amount')

    ns_fr = fields.Selection([
        ('IFRS', 'IFRS'),
        ('GAAP', 'GAAP')
    ], string='FR', help='Affect Financial Report by IFRS/GAAP method')

    @api.depends('debit', 'credit', 'company_currency_id','date')
    def _compute_usd_budget_amount(self):
        for rec in self:
            rec.ns_debit_usd_budget = rec.debit
            rec.ns_credit_usd_budget = rec.credit

            if rec.company_currency_id.id != rec.ns_usd_currency_id.id:
                currency_rates = self.env['crm.fx.rate'].sudo().search([('currency_id','=',rec.company_currency_id.id), ('date_start','<=',rec.date), ('date_end','>=',rec.date)],limit=1)
                        
                if not currency_rates:
                    currency_rates = self.env['crm.fx.rate'].sudo().search([('currency_id','=',rec.company_currency_id.id)],order='id DESC',limit=1)
                
                if currency_rates:
                    rec.ns_debit_usd_budget = rec.debit / currency_rates.rate
                    rec.ns_credit_usd_budget = rec.credit / currency_rates.rate

    @api.depends('debit', 'credit', 'company_currency_id','date')
    def _compute_usd_real_amount(self):
        for rec in self:
            rec.ns_debit_usd_real = rec.debit
            rec.ns_credit_usd_real = rec.credit

            if rec.company_currency_id.id != rec.ns_usd_currency_id.id:
                currency_rates = rec.ns_usd_currency_id._get_rates(rec.company_id, rec.date)
                rec.ns_debit_usd_real = rec.debit * currency_rates.get(rec.ns_usd_currency_id.id)
                rec.ns_credit_usd_real = rec.credit * currency_rates.get(rec.ns_usd_currency_id.id)

    @api.model
    def recalculate_usd_budge(self):
        print('recalculate_usd_budge_and_real_amount====')
        move_lines = self.search([])
        for m_line in move_lines:
            print(m_line)
            m_line._compute_usd_budget_amount()

    