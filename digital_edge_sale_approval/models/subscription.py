from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class SubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute')

    
class Subscription(models.Model):
    _inherit = "sale.subscription"

    def _prepare_invoice_data(self):
        res = super(Subscription, self)._prepare_invoice_data()
        res['ns_billing_contact'] = self.x_studio_original_sales_order.x_studio_billing_contact_1.id

        return res

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        res = super(Subscription, self)._prepare_invoice_line(line, fiscal_position, date_start=date_start, date_stop=date_stop)
        res['ns_product_attribute_value'] = line.ns_product_attribute_value.id

        return res
