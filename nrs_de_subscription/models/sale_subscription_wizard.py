# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = 'sale.subscription.wizard'

    def create_sale_order(self):
        self = self.with_company(self.subscription_id.company_id)
        fpos = self.env['account.fiscal.position'].get_fiscal_position(
            self.subscription_id.partner_id.id)
        sale_order_obj = self.env['sale.order']
        team = self.env['crm.team']._get_default_team_id(user_id=self.subscription_id.user_id.id)
        origin_sale_order = self.subscription_id.x_studio_original_sales_order
        new_order_vals = {
            'partner_id': self.subscription_id.partner_id.id,
            'analytic_account_id': self.subscription_id.analytic_account_id.id,
            'team_id': team and team.id,
            'pricelist_id': self.subscription_id.pricelist_id.id,
            'payment_term_id': self.subscription_id.payment_term_id.id,
            'fiscal_position_id': fpos.id,
            'subscription_management': 'upsell',
            'origin': self.subscription_id.code,
            'company_id': self.subscription_id.company_id.id,
            'x_studio_operation_country': origin_sale_order.x_studio_operation_country.id,
            'x_studio_operation_metro': origin_sale_order.x_studio_operation_metro.id,
            'x_studio_operation_site': origin_sale_order.x_studio_operation_site.id,
            'x_studio_capacity_manager': origin_sale_order.x_studio_capacity_manager.id,
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.subscription_id.partner_id.property_payment_term_id:
            new_order_vals['payment_term_id'] = self.subscription_id.partner_id.property_payment_term_id.id
        order = sale_order_obj.create(new_order_vals)
        order.message_post(body=(_("This upsell order has been created from the subscription ") + " <a href=# data-oe-model=sale.subscription data-oe-id=%d>%s</a>" % (self.subscription_id.id, self.subscription_id.display_name)))
        for line in self.option_lines:
            self.subscription_id.partial_invoice_line(order, line, date_from=self.date_from)
        order.order_line._compute_tax_id()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order.id,
        }

class SaleSubscriptionWizardOption(models.TransientModel):
    _inherit = "sale.subscription.wizard.option"

    product_template_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    is_update_subscription = fields.Boolean(default=False, readonly=True)
    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute')
    product_id = fields.Many2one('product.product', domain="")

    @api.onchange("product_id")
    def onchange_product_id(self):
        if not self.product_id:
            return
        else:
            self.name = self.product_id.get_product_multiline_description_sale()

            if not self.uom_id or self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = self.product_id.uom_id.id

    @api.onchange('product_template_id')
    def update_product_attribute_domain(self):
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        order_id = subscription.x_studio_original_sales_order
        if self.product_template_id.ns_standard_product == 'no':
            return {'warning': {'title': _('Warning'), 'message': _('You have chosen a non-standard product')}}
        if self.product_template_id.ns_standard_product == 'depend':
            allowed_attribute = []
            attr_products = self.env['ns.product.product.attr'].search(
                [('ns_product_id', '=', self.product_template_id.id),
                 ('ns_operation_site', '=', order_id.x_studio_operation_site.id)])
            for attribute in attr_products:
                allowed_attribute.append(attribute.ns_product_attribute_value.id)
            return {
                'domain': {'ns_product_attribute_value': [('id', 'in', allowed_attribute)]}
            }

    @api.onchange('ns_product_attribute_value')
    def check_product_attribute(self):
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        order_id = subscription.x_studio_original_sales_order
        if self.product_template_id:
            if self.product_template_id.ns_standard_product == 'depend':
                attr_products = self.env['ns.product.product.attr'].search(
                    [('ns_product_id', '=', self.product_template_id.id),
                     ('ns_operation_site', '=', order_id.x_studio_operation_site.id),
                     ('ns_product_attribute_value', '=', self.ns_product_attribute_value.id)])
                if attr_products:
                    for attr in attr_products:
                        if not attr.ns_standard:
                            return {'warning': {'title': _('Warning'),
                                                'message': _('You have chosen a non-standard product attribute')}}
                else:
                    return {'warning': {'title': _('Warning'), 'message': _(
                        'This product-product attribute combination has not been created. Please contact Product Team')}}
