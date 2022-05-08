# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class TaskInherit(models.Model):
    _inherit = "project.task"

    nrs_sale_order = fields.Many2one('sale.order','Sale order', related='sale_line_id.order_id')
    nrs_a_end_service_id = fields.Many2one('project.task','A-End Service ID', related='nrs_sale_order.nrs_a_end_service_id')
    nrs_z_end_service_id = fields.Char('Z-End Service ID', related='nrs_sale_order.nrs_z_end_service_id')
    nrs_patch_panel_id = fields.Char('Patch Panel ID', related='nrs_sale_order.nrs_patch_panel_id')
    # nrs_port_number = fields.Char('Port Number', related='nrs_sale_order.nrs_port_number')
    ns_port_number = fields.Char('Port Number', related='nrs_sale_order.ns_port_number')

    def _compute_service_id(self):
        for project in self:
            temp_name = project.name
            project.ns_service_id = temp_name
            if project.x_studio_product.ns_capacity_assignation == 'space_id':
                if project.x_studio_space_id.ns_name:
                    project.ns_service_id = temp_name + " / " + str(project.x_studio_space_id.ns_name)
            elif project.x_studio_product.ns_capacity_assignation == 'breaker_id' or project.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                if project.x_studio_related_space_id.ns_name:
                    project.ns_service_id = temp_name + " / " + str(project.x_studio_related_space_id.ns_name)