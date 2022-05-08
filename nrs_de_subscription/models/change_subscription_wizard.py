# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class ChangeSubscriptionWizard(models.TransientModel):
    _name = 'change.subscription.wizard'
    _description = 'Subscription Change wizard'

    def _default_subscription(self):
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        return subscription

    def _get_items_from_subscription(self):
        line_vals = []
        change_order_line_obj = self.env['change.subscription.wizard.line']
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        if subscription:
            for line in subscription.recurring_invoice_line_ids:
                change_order_vals = {
                    'ns_subscription_line_id' : line.id,
                    'wizard_id': self.id,
                    'name': line.name,
                    'product_id': line.product_id,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id,
                    'unit_price': line.price_unit,
                    'discount': line.discount,
                    'ns_product_attribute_value': line.ns_product_attribute_value,
                    'ns_product_attribute_value_origin' : line.ns_product_attribute_value,
                    'ns_sale_line_id': line.ns_sale_line_id,
                    'ns_sub_task_id': line.ns_sub_task_id,
                }
                line_vals.append((0,0, change_order_vals))
        return line_vals

    subscription_id = fields.Many2one('sale.subscription', string="Subscription", required=True,
                                      default=_default_subscription, ondelete="cascade")
    change_order_lines = fields.One2many('change.subscription.wizard.line', 'wizard_id', string="Subscription Lines", default=_get_items_from_subscription)
    date_from = fields.Date("Start Date", default=fields.Date.today,
                            help="The discount applied when creating a sales order will be computed as the ratio between "
                                 "the full invoicing period of the subscription and the period between this date and the "
                                 "next invoicing date.")

    def create_sale_order(self):
        self = self.with_company(self.subscription_id.company_id)
        fpos = self.env['account.fiscal.position'].get_fiscal_position(
            self.subscription_id.partner_id.id)
        sale_order_obj = self.env['sale.order']
        team = self.env['crm.team']._get_default_team_id(user_id=self.subscription_id.user_id.id)
        origin_sale_order = self.subscription_id.x_studio_original_sales_order
        subs_code = self.subscription_id.code
        orders = self.env['sale.order'].search([('name', 'ilike', subs_code + "-CO")])
        name = "%s-CO%s" % (subs_code, len(orders) + 1)
        new_order_vals = {
            'name': name,
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
            'ns_is_change_order': True,
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.subscription_id.partner_id.property_payment_term_id:
            new_order_vals['payment_term_id'] = self.subscription_id.partner_id.property_payment_term_id.id
        order = sale_order_obj.create(new_order_vals)
        order.message_post(body=(_("This upsell order has been created from the subscription ") + " <a href=# data-oe-model=sale.subscription data-oe-id=%d>%s</a>" % (self.subscription_id.id, self.subscription_id.display_name)))
        for line in self.change_order_lines:
            self.subscription_id.partial_invoice_line(order, line, date_from=self.date_from)
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order.id,
        }

class ChangeSubscriptionWizardLine(models.TransientModel):
    _name = "change.subscription.wizard.line"
    _description = 'Subscription Change Lines Wizard'

    name = fields.Char(string="Description")
    wizard_id = fields.Many2one('change.subscription.wizard', required=True, ondelete="cascade")
    ns_subscription_line_id = fields.Many2one('sale.subscription.line', string='Subscription Line', required=True)
    product_id = fields.Many2one('product.product', required=True, domain="[('recurring_invoice', '=', True)]", ondelete="cascade")
    product_template_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, ondelete="cascade", domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price', required=True, digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    is_update_subscription = fields.Boolean(default=True, readonly=True)
    ns_product_attribute_value_origin = fields.Many2one('product.attribute.value', string='Product Attribute Origin')
    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute')
    ns_product_attribute_domain = fields.Many2many('product.attribute.value', 'change_subscription_wizard_rel',
                                                   compute='_compute_product_attribute_domain')
    ns_sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    ns_sub_task_id = fields.Many2many('project.task', string='Installed Base Service ID')

    @api.depends('product_template_id')
    def _compute_product_attribute_domain(self):
        for change_order_line in self:
            attribute_ids = []
            subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
            order_id = subscription.x_studio_original_sales_order
            if change_order_line.product_template_id.ns_standard_product == 'depend':
                attr_products = self.env['ns.product.product.attr'].search(
                    [('ns_product_id', '=', change_order_line.product_template_id.id),
                     ('ns_operation_site', '=', order_id.x_studio_operation_site.id)])
                for attribute in attr_products:
                    attribute_ids.append((4, attribute.ns_product_attribute_value.id))
            else:
                attr_products = self.env['ns.product.product.attr'].search([])
                for attribute in attr_products:
                    attribute_ids.append((4, attribute.ns_product_attribute_value.id))

            change_order_line.ns_product_attribute_domain = attribute_ids

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
                 ('ns_operation_site', '=', self.order_id.x_studio_operation_site.id)])
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
