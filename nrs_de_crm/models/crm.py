from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CRM_Lead(models.Model):
    _inherit = 'crm.lead'

    ns_currency_rate = fields.Float("Currency Rate", compute="_compute_current_currency_rate", readonly=True)

    @api.depends('mrc_nrc_currency_id', 'recurring_revenue', 'recurring_revenue_usd')
    def _compute_current_currency_rate(self):
        for rec in self:
            if rec.recurring_revenue_usd != 0:
                rec.ns_currency_rate = rec.recurring_revenue / rec.recurring_revenue_usd
            else:
                rec.ns_currency_rate = 0
            
    @api.depends('ns_currency_rate')
    def _compute_mrc_nrc(self):
        super(CRM_Lead, self)._compute_mrc_nrc()

    @api.onchange('user_id')
    def onchange_salesperson(self):
        self.x_studio_a_end_sales = self.user_id

    def action_sale_quotations_new(self):
        for lead in self:
            for order in lead.order_ids:
                if order.state in ['draft', 'preapproved', 'approved', 'sent', 'sale', 'done']:
                    raise UserError('You cannot have more than one quotation in one opportunity.Create '
                                    'another opportunity or modify the existing one')
        return super(CRM_Lead, self).action_sale_quotations_new()
