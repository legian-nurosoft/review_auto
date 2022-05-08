# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_date_to_confirm = fields.Date(string='Date to Confirm', readonly=True)
    subscription_management = fields.Selection(selection_add=[('upsell', 'Change Order')])
    x_contract_term = fields.Integer(string="Contract Terms (months)", default=12)
    x_operating_sites = fields.Many2one("operating.sites", string="Operating Sites")

    @api.model
    def _cron_auto_confirm_quotaion(self):
        sale_orders = self.search([('x_date_to_confirm', '=', date.today()), ('state', 'in', ['draft', 'sent'])])
        for sale_order in sale_orders:
            sale_order.action_confirm()

    def _prepare_subscription_data(self, template):
        res = super()._prepare_subscription_data(template)
        default_stage = self.env['sale.subscription.stage'].search([('category', '=', 'draft')], limit=1)

        if default_stage:
            res['stage_id'] = default_stage.id
        res['date_start'] = False
        res['code'] = self and self.name or ''
        res['recurring_next_date'] = False
        res['recurring_invoice_day'] = False
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('x_contract_term'):
            related_subscriptions  = self.order_line.mapped('subscription_id')
            if related_subscriptions:
                related_subscriptions._compute_contract_end_date()
        return res
