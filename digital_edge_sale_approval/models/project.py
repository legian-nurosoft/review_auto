from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute', related='sale_line_id.ns_product_attribute_value')
