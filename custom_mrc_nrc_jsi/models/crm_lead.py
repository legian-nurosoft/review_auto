# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'

    mrc_nrc_currency_id = fields.Many2one('res.currency', 'Currency(MRC/NRC)')
    expected_revenue_usd = fields.Float('NRC(USD)', compute='_compute_mrc_nrc', store=True, readonly=True)
    recurring_revenue_usd = fields.Float('MRC(USD)', compute='_compute_mrc_nrc', store=True, readonly=True)

    x_studio_oppt_kva = fields.Float(string='Oppt kVA', digits='Oppt kVA')
    x_studio_oppt_kva_committed = fields.Float(string='Oppt kVA Committed', digits='Oppt kVA')

    #add new Domain
    partner_id = fields.Many2one(
        'res.partner', string='Customer', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('nrs_company_type', '!=', 'person')]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")

    @api.depends('stage_id', 'expected_revenue', 'recurring_revenue')
    def _compute_mrc_nrc(self):
        fx_rate = self.env['crm.fx.rate']
        for lead in self:
            if lead.won_status not in ['won', 'lost']:
                expected_revenue_usd = recurring_revenue_usd = 0.00
                current_date = str(fields.Date.context_today(self))
                current_rate = fx_rate.search([('date_start', '<=', current_date), ('currency_id', '=', lead.mrc_nrc_currency_id.id), ('date_end', '>=', current_date)], order='date_start desc', limit=1)
                
                if current_rate:
                    if lead.expected_revenue:
                        expected_revenue_usd = lead.expected_revenue / current_rate.rate
                    if lead.recurring_revenue:
                        recurring_revenue_usd = lead.recurring_revenue / current_rate.rate
                    lead.update({
                        'expected_revenue_usd': expected_revenue_usd,
                        'recurring_revenue_usd': recurring_revenue_usd,
                    })
