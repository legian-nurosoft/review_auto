# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_mrc = fields.Float('MRC', compute='_compute_mrc_nrc', readonly=True)
    amount_nrc = fields.Float('NRC', compute='_compute_mrc_nrc', readonly=True)

    # DE44 Dev 2
    ns_total_usd_mrc = fields.Float(string='Total USD MRC', compute='_compute_usd_mrc_nrc', readonly=True)
    ns_total_usd_nrc = fields.Float(string='Total USD NRC', compute='_compute_usd_mrc_nrc', readonly=True)

    @api.depends('order_line.price_total')
    def _compute_mrc_nrc(self):
        for order in self:
            line_with_subscription_product = order.order_line.filtered(lambda x: x.product_id.recurring_invoice)
            line_without_subscription_product = order.order_line - line_with_subscription_product
            amount_mrc = line_with_subscription_product and sum(line_with_subscription_product.mapped('price_subtotal')) or 0.0
            amount_nrc = line_without_subscription_product and sum(line_without_subscription_product.mapped('price_subtotal')) or 0.0
            order.update({
                'amount_mrc': amount_mrc,
                'amount_nrc': amount_nrc,
            })

    @api.depends('amount_mrc', 'amount_nrc', 'currency_id')
    def _compute_usd_mrc_nrc(self):
        fx_rate = self.env['crm.fx.rate']
        for rec in self:
            current_date = str(fields.Date.context_today(self))
            current_rate = fx_rate.search([('date_start', '<=', current_date), ('currency_id', '=', rec.currency_id.id),
                                           ('date_end', '>=', current_date)], order='date_start desc', limit=1)
            if current_rate:
                rec.update({
                    'ns_total_usd_mrc': rec.amount_mrc / current_rate.rate,
                    'ns_total_usd_nrc': rec.amount_nrc / current_rate.rate
                })
            else:
                rec.update({
                    'ns_total_usd_mrc': False,
                    'ns_total_usd_nrc': False
                })


    @api.model
    def create(self, vals):
        if vals.get('opportunity_id',False):
            crm = self.env['crm.lead'].sudo().browse(vals.get('opportunity_id',False))
            if crm and crm.mrc_nrc_currency_id:
                fx_rate = self.env['crm.fx.rate'].sudo().search([('currency_id','=',crm.mrc_nrc_currency_id.id)],limit=1)
                if fx_rate:
                    vals['x_studio_crm_fx_rate'] = fx_rate.id

        return super(SaleOrder, self).create(vals)