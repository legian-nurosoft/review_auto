# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Task(models.Model):
    _inherit = "project.task"

    ns_change_order_line_id = fields.Many2one('sale.order.line', 'Change Order Line')
    ns_updated_product_attribute_value = fields.Many2one('product.attribute.value', string='Updated Product Attribute', compute='_compute_updated_attribute_value')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Task, self).create(vals_list)
        for task in res:          
            if task.parent_id:              
                task.parent_id.write({'x_studio_sub_tasks': [(4,task.id)]})
            
        return res

    @api.depends('ns_change_order_line_id')
    def _compute_updated_attribute_value(self):
        for rec in self:
            if rec.ns_change_order_line_id:
                rec.ns_updated_product_attribute_value = rec.ns_change_order_line_id.ns_product_attribute_value.id
            else:
                rec.ns_updated_product_attribute_value = rec.ns_product_attribute_value.id
