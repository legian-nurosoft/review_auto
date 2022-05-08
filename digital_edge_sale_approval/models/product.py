from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ns_standard_product = fields.Selection([
            ('yes','Yes'),
            ('no','No'),
            ('depend','Depend')
        ], string='Standard Product', default='yes')

    ns_product_attribute = fields.Many2one('product.attribute', string='Product Attribute')
    ns_show_custom_attribute_value = fields.Boolean(string='Show Custom Attribute Value')


class ProductAtrribute(models.Model):
    _name = 'ns.product.product.attr'
    _description = "Product-Product Attribute Combination"
    _rec_name = 'ns_name'

    ns_name = fields.Char(string='Name')
    ns_product_id = fields.Many2one('product.template', string='Product')
    ns_product_attribute_type = fields.Many2one('product.attribute', string='Product Attribute Type', related='ns_product_id.ns_product_attribute')
    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Attribute Value')
    ns_operation_site = fields.Many2one('operating.sites', string='Operation Site')
    ns_standard = fields.Boolean(string='Standard')

    