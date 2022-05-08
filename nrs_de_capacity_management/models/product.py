from odoo import api, models, api, exceptions, fields, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ns_capacity_assignation = fields.Selection([
            ('space_id', 'Space ID'),
            ('breaker_id', 'Breaker ID'),
            ('patch_panel_id', 'Patch Panel ID'),
            ('port_id', 'Port ID')
        ], string='Capacity Assignation')