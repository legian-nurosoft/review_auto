from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"


    ns_amount_mrc = fields.Monetary('MRC', compute='_compute_mrc_nrc', readonly=True)
    ns_amount_nrc = fields.Monetary('NRC', compute='_compute_mrc_nrc', readonly=True)

    ns_tax_mrc = fields.Monetary('Tax MRC', compute='_compute_mrc_nrc', readonly=True)
    ns_tax_nrc = fields.Monetary('Tax NRC', compute='_compute_mrc_nrc', readonly=True)

    @api.depends('invoice_line_ids.price_total')
    def _compute_mrc_nrc(self):
        for move in self:
            line_with_subscription_product = move.invoice_line_ids.filtered(lambda x: x.product_id.recurring_invoice)
            line_without_subscription_product = move.invoice_line_ids - line_with_subscription_product
            amount_mrc = line_with_subscription_product and sum(line_with_subscription_product.mapped('price_subtotal')) or 0.0
            amount_nrc = line_without_subscription_product and sum(line_without_subscription_product.mapped('price_subtotal')) or 0.0
            move.update({
                'ns_amount_mrc': amount_mrc,
                'ns_amount_nrc': amount_nrc,
                'ns_tax_mrc': amount_mrc * 0.1,
                'ns_tax_nrc': amount_nrc * 0.1,
            })
