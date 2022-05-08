# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo import tools

class BillingPreview(models.Model):
    _name = "ns.billing.preview"
    _description = "Billing Preview"
    _auto = False
    _rec_name = 'ns_recurring_next_date'
    _order = 'ns_company_id asc, ns_recurring_next_date asc, ns_count desc'

    ns_recurring_next_date = fields.Date(string='Date of Next Invoice')
    ns_company_id = fields.Many2one('res.company', string='Company')
    ns_count = fields.Integer(string='Count')
    ns_detail_id = fields.One2many('ns.billing.preview.detail', 'ns_billing_preview_id')

    @property
    def _table_query(self):
        return '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())

    @api.model
    def _select(self):
        return """
            SELECT
                CONCAT(EXTRACT(DOY FROM s_subs.recurring_next_date), EXTRACT(YEAR FROM s_subs.recurring_next_date), s_subs.company_id)::INT AS id,
                count(s_subs_line.id) AS ns_count,
                s_subs.recurring_next_date AS ns_recurring_next_date,
                s_subs.company_id AS ns_company_id
                
        """

    @api.model
    def _from(self):
        return """
            FROM sale_subscription AS s_subs
            JOIN sale_subscription_line AS s_subs_line ON s_subs.id = s_subs_line.analytic_account_id
            JOIN sale_subscription_stage AS s_subs_stage ON s_subs_stage.id = s_subs.stage_id
        """

    @api.model
    def _where(self):
        return """
            WHERE 
                s_subs_stage.category = 'progress' AND
                s_subs.recurring_next_date IS NOT NULL
        """

    @api.model
    def _group_by(self):
        return """
            GROUP BY
                s_subs.recurring_next_date,
                s_subs.company_id
        """


class BillingPreviewDetail(models.Model):
    _name = "ns.billing.preview.detail"
    _description = "Billing Preview Detail"
    _auto = False
    _order = "ns_original_sales_order_id asc"

    ns_billing_preview_id = fields.Many2one('ns.billing.preview')
    ns_subscription_line_id = fields.Many2one('sale.subscription.line', string='Subscription Line')
    ns_partner_id = fields.Many2one('res.partner', string='Customer')
    ns_original_sales_order_id = fields.Many2one('sale.order', string='Sales Order')
    ns_start_date = fields.Date(string='Start Date', compute='_compute_data')
    ns_subscription_start_date = fields.Date(string='Service Charge Period: From', compute='_compute_data')
    ns_subscription_end_date = fields.Date(string='Service Charge Period: To', compute='_compute_data')
    ns_operation_site_id = fields.Many2one('operating.sites', string='Site', compute='_compute_data')
    ns_product_id = fields.Many2one('product.product', string='Product', compute='_compute_data')
    ns_product_code = fields.Char(string='Product Code', related='ns_product_id.default_code')
    ns_product_name = fields.Char(string='Description', related='ns_product_id.name')
    ns_quantity = fields.Float(string='Qty', digits='Product Unit of Measure', compute='_compute_data')
    ns_uom_id = fields.Many2one('uom.uom', string='Unit', compute='_compute_data')
    ns_price_unit = fields.Float(string='Unit Cost', digits='Product Price', compute='_compute_data')
    ns_mrc_price_unit = fields.Float(string='MRC', digits='Product Price', compute='_compute_data')
    ns_nrc_price_unit = fields.Float(string='NRC', digits='Product Price', compute='_compute_data')
    ns_tax_id = fields.Many2many('account.tax', string='Taxes', compute='_compute_data')
    ns_currency_id = fields.Many2one('res.currency', string='Billing Currency', compute='_compute_data')
    ns_tax = fields.Monetary(currency_field='ns_currency_id', string='Total Tax', compute='_compute_data')
    ns_total = fields.Monetary(currency_field='ns_currency_id', string='Grand Total', compute='_compute_data')

    def _compute_data(self):
        for rec in self:
            rec.ns_start_date = rec.ns_subscription_line_id.analytic_account_id.date_start
            rec.ns_operation_site_id = rec.ns_original_sales_order_id.x_studio_operation_site.id
            rec.ns_product_id = rec.ns_subscription_line_id.product_id.id
            rec.ns_quantity = rec.ns_subscription_line_id.quantity
            rec.ns_uom_id = rec.ns_subscription_line_id.uom_id.id
            rec.ns_price_unit = rec.ns_subscription_line_id.price_unit
            rec.ns_mrc_price_unit = rec.ns_subscription_line_id.price_unit
            rec.ns_currency_id = rec.ns_subscription_line_id.currency_id.id
            
            move_line = self.env['account.move.line'].search([('subscription_id','=',rec.ns_subscription_line_id.analytic_account_id.id)], limit=1)
            if move_line:
                rec.ns_subscription_start_date = move_line.subscription_start_date
                rec.ns_subscription_end_date = move_line.subscription_end_date
            else:
                rec.ns_subscription_start_date = False
                rec.ns_subscription_end_date = False

            nrc_price_unit = 0
            for nrc in rec.ns_subscription_line_id.analytic_account_id.ns_nrc_line_ids:
                if nrc.product_id.id == rec.ns_product_id.id:
                    nrc_price_unit = nrc.price_unit
            rec.ns_nrc_price_unit = nrc_price_unit

            taxes = []
            for order_line in rec.ns_original_sales_order_id.order_line:
                if order_line.product_id.id == rec.ns_product_id.id:
                    for tax in order_line.tax_id:
                        taxes.append((4,tax.id))

            rec.ns_tax_id = taxes
            tax_values = rec.ns_tax_id.compute_all(
                        rec.ns_price_unit,
                        currency=rec.ns_currency_id,
                        quantity=rec.ns_quantity,
                        product=rec.ns_product_id,
                        partner=rec.ns_partner_id)

            rec.ns_total = tax_values['total_included']
            rec.ns_tax = tax_values['total_included'] - tax_values['total_excluded']


    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return """
            SELECT
                s_subs_line.id AS id,
                s_subs_line.id AS ns_subscription_line_id,
                CONCAT(EXTRACT(DOY FROM s_subs.recurring_next_date), EXTRACT(YEAR FROM s_subs.recurring_next_date), s_subs.company_id)::INT AS ns_billing_preview_id,
                s_subs.partner_id AS ns_partner_id,
                s_subs.x_studio_original_sales_order AS ns_original_sales_order_id
        """

    @api.model
    def _from(self):
        return """
            FROM sale_subscription_line AS s_subs_line
            JOIN sale_subscription AS s_subs ON s_subs.id = s_subs_line.analytic_account_id
            JOIN sale_subscription_stage AS s_subs_stage ON s_subs_stage.id = s_subs.stage_id
            JOIN product_product AS product ON product.id = s_subs_line.product_id
        """

    @api.model
    def _where(self):
        return """
            WHERE 
                s_subs_stage.category = 'progress' AND
                s_subs.recurring_next_date IS NOT NULL AND
                product.active = true
        """