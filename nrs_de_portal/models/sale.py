# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # nrs_a_end_service_id = fields.Many2one('project.task','A-End Service ID')
    # nrs_a_end_service_id = fields.Many2one('project.task','A-End Service ID')
    # nrs_z_end_service_id = fields.Char('Z-End Service ID')
    # nrs_loa = fields.Binary('Letter of Authorization (LOA)')
    # crd_contract_required = fields.Boolean('is crd and contract required ?', default=True)
    # nrs_patch_panel_id = fields.Char('Patch Panel ID')
    # nrs_port_number = fields.Char('Port Number')

    nrs_a_end_service_id = fields.Many2one('project.task','A-End Service ID')
    nrs_z_end_service_id = fields.Char('Z-End Service ID')
    nrs_loa = fields.Binary('Letter of Authorization (LOA)')
    crd_contract_required = fields.Boolean('is crd and contract required ?', default=True)
    nrs_patch_panel_id = fields.Char('Patch Panel ID')
    ns_port_number = fields.Char('Port Number')
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    nrs_a_end_service_id = fields.Many2one('project.task','A-End Service ID')
    nrs_z_end_service_id = fields.Char('Z-End Service ID')
    nrs_loa = fields.Binary('Letter of Authorization (LOA)')
    nrs_patch_panel_id = fields.Char('Patch Panel ID')
    ns_port_number = fields.Char('Port Number')

    