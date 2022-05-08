from odoo import api, models, api, exceptions, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ns_has_reserved_space_or_breaker = fields.Boolean('Has reserved space or breaker',
                                                      compute='_compute_reserved_space_or_breaker')
    ns_can_assign_capacity = fields.Boolean('Can assign capacity', compute='_compute_ns_can_assign_capacity')
    ns_capacity_button_visibility = fields.Boolean('Display Capacity Assign Button',
                                                   compute='_compute_button_visibility')
    ns_capacity_button_port_visibility = fields.Boolean('Display Port Assign Button',
                                                   compute='_compute_button_port_visibility')

    def _compute_button_visibility(self):
        """In here we check the status of the record only and
        separated the display logic from other field dependancies"""
        for record in self:
            if record.product_template_id.ns_capacity_assignation in ['space_id', 'breaker_id']:
                if record.order_id.approval_state not in ['sale', 'done', 'draft']:
                    record.ns_capacity_button_visibility = True
                else:
                    record.ns_capacity_button_visibility = False
            else:
                record.ns_capacity_button_visibility = False
                
    def _compute_button_port_visibility(self):
        """In here we check the status of the record only and
        separated the display logic from other field dependancies"""
        for record in self:
            if record.product_template_id.ns_capacity_assignation in ['port_id', 'patch_panel_id']:
                if record.order_id.approval_state not in ['sale', 'done', 'draft']:
                    record.ns_capacity_button_port_visibility = True
                else:
                    record.ns_capacity_button_port_visibility = False
            else:
                record.ns_capacity_button_port_visibility = False

    def _compute_ns_can_assign_capacity(self):
        for rec in self:
            rec.ns_can_assign_capacity = True if rec.order_id.approval_state in ['preapproved', 'approved',
                                                                                 'sent'] else False

    def _compute_reserved_space_or_breaker(self):
        for rec in self:
            value = False
            if rec.product_template_id.ns_capacity_assignation in ['space_id', 'breaker_id']:
                if rec.product_template_id.ns_capacity_assignation == 'space_id':
                    reserved_spaces = self.env['ns.ns_space'].search(
                        [('ns_reserved', '=', True), ('ns_sale_order_line_id', '=', rec.id)])
                    if reserved_spaces:
                        value = True

                elif rec.product_template_id.ns_capacity_assignation == 'breaker_id':
                    reserved_breaker = self.env['ns.ns_breaker'].search(
                        [('ns_reserved', '=', True), ('ns_sale_order_line_id', '=', rec.id)])
                    if reserved_breaker:
                        value = True

            else:
                value = True

            rec.ns_has_reserved_space_or_breaker = value

    def assign_capacity(self):
        show_wizard = False
        wizard_id = False
        wizard_title = ''
        if self.product_template_id.ns_capacity_assignation == 'space_id':
            space_ids = []
            show_wizard = True
            wizard_title = _('Please select the space')
            line = []
            selected_line = []
            available_spaces = self.env['ns.ns_space'].search(
                [('ns_operation_site', '=', self.order_id.x_studio_operation_site.id), ('ns_sold', '=', False),
                 ('ns_reserved', '=', False)])
            selected_spaces = self.env['ns.ns_space'].search(
                [('ns_sale_order_line_id', '=', self.id),
                 ('ns_reserved', '=', True)])

            for space in available_spaces:
                line.append((0, 0, {'ns_space_id': space.id}))
                space_ids.append((4, space.id))
            
            for space in selected_spaces:
                selected_line.append((0, 0, {'ns_space_id': space.id, 'ns_selected': True}))

            
            wizard_id = self.env['ns.space.breaker.wizard'].create({
                'ns_order_line_id': self.id,
                'ns_type': 'space',
                'ns_space_ids': selected_line,
                'ns_space_ids_unselected':line,
                'ns_space_search_helper_ids': space_ids
            })

        if self.product_template_id.ns_capacity_assignation == 'breaker_id':
            breaker_ids = []
            show_wizard = True
            wizard_title = _('Please select the breaker')
            line = []
            selected_line = []
            available_breakers = self.env['ns.ns_breaker'].search(
                [('ns_pdu.ns_operation_site', '=', self.order_id.x_studio_operation_site.id), ('ns_sold', '=', False),
                 ('ns_reserved', '=', False)])
            selected_breakers = self.env['ns.ns_breaker'].search(
                [('ns_sale_order_line_id', '=', self.id),
                 ('ns_reserved', '=', True)])

            for breaker in available_breakers:
                line.append((0, 0, {'ns_breaker_id': breaker.id}))
                breaker_ids.append((4, breaker.id))
            
            for breaker in selected_breakers:
                selected_line.append((0, 0, {'ns_breaker_id': breaker.id, 'ns_selected': True}))

            
            wizard_id = self.env['ns.space.breaker.wizard'].create({
                'ns_order_line_id': self.id,
                'ns_type': 'breaker',
                'ns_breaker_ids': selected_line,
                'ns_breaker_ids_unselected':line,
                'ns_breaker_search_helper_ids':breaker_ids,
            })

        if show_wizard:
            return {
                'name': wizard_title,
                'view_mode': 'form',
                'res_model': 'ns.space.breaker.wizard',
                'type': 'ir.actions.act_window',
                'res_id': wizard_id.id,
                'target': 'new'
            }
    
    def assign_patchpanelport(self):
        """pop up wizard to assign patch panel and port"""
        show_wizard = False
        wizard_id = False
        wizard_title = ''
        if self.product_template_id.ns_capacity_assignation == 'patch_panel_id':
            patch_ids = []
            show_wizard = True
            wizard_title = _('Please select the Patch Panel')
            line = []
            selected_line = []
            available_patchs = self.env['ns.ns_patchpanel'].search(
                [('ns_operation_site', '=', self.order_id.x_studio_operation_site.id),
                 ('ns_stage', '=', 'Available')])
            selected_patchs = self.env['ns.ns_patchpanel'].search(
                [('ns_sale_order_line_id', '=', self.id),
                 ('ns_stage', '=', 'Assigned')])

            for patch in available_patchs:
                line.append((0, 0, {'ns_patch_id': patch.id}))
                patch_ids.append((4, patch.id))
            
            for patch in selected_patchs:
                selected_line.append((0, 0, {'ns_patch_id': patch.id, 'ns_selected': True}))

            
            wizard_id = self.env['ns.space.breaker.wizard'].create({
                'ns_order_line_id': self.id,
                'ns_type': 'patch_panel',
                'ns_patch_ids': selected_line,
                'ns_patch_ids_unselected':line,
                'ns_patch_search_helper_ids': patch_ids
            })

        if self.product_template_id.ns_capacity_assignation == 'port_id':
            port_ids = []
            show_wizard = True
            wizard_title = _('Please select the Ports')
            line = []
            selected_line = []
            available_ports = self.env['ns.ns_ports'].search(
                [('ns_operation_site', '=', self.order_id.x_studio_operation_site.id),
                 ('ns_stage', '=', 'Available')])
            selected_ports = self.env['ns.ns_ports'].search(
                [('ns_sale_order_line_id', '=', self.id),
                 ('ns_stage', '!=', 'Assigned')])

            for port in available_ports:
                line.append((0, 0, {'ns_port_id': port.id}))
                port_ids.append((4, port.id))
            
            for port in selected_ports:
                selected_line.append((0, 0, {'ns_port_id': port.id, 'ns_selected': True}))

            
            wizard_id = self.env['ns.space.breaker.wizard'].create({
                'ns_order_line_id': self.id,
                'ns_type': 'port',
                'ns_port_ids': selected_line,
                'ns_port_ids_unselected':line,
                'ns_port_search_helper_ids':port_ids,
            })

        if show_wizard:
            return {
                'name': wizard_title,
                'view_mode': 'form',
                'res_model': 'ns.space.breaker.wizard',
                'type': 'ir.actions.act_window',
                'res_id': wizard_id.id,
                'target': 'new'
            }

    def _timesheet_create_task_prepare_values(self, project):
        result = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        if self.product_template_id.ns_capacity_assignation == 'space_id':
            reserved_spaces = self.env['ns.ns_space'].search(
                [('ns_reserved', '=', True), ('ns_sale_order_line_id', '=', self.id), ('ns_sold', '=', False)])
            if reserved_spaces:
                result['x_studio_space_id'] = reserved_spaces[0].id

        elif self.product_template_id.ns_capacity_assignation == 'breaker_id':
            reserved_breaker = self.env['ns.ns_breaker'].search(
                [('ns_reserved', '=', True), ('ns_sale_order_line_id', '=', self.id), ('ns_sold', '=', False)])
            if reserved_breaker:
                result['x_studio_breaker_id'] = reserved_breaker[0].id
        return result
    
        
    def action_open_sale_order_line_shortcut(self):
        """shortcut to open so line form view"""
        self.ensure_one()
        form_id = self.env.ref('nrs_de_portal.sale_order_line_view_form').id
        return {'name': 'Sale Order Line',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order.line',
                'views': [(form_id, 'form')],
                'target': 'new',
                'res_id': self.id
                }
    

class SpaceLineWizard(models.TransientModel):
    _name = 'ns.space.wizard.line'

    ns_wizard_id = fields.Many2one('ns.space.breaker.wizard')
    ns_wizard_id_selected = fields.Many2one('ns.space.breaker.wizard')
    ns_selected = fields.Boolean('Select', store=True)
    ns_space_id = fields.Many2one('ns.ns_space', 'Space')


class BreakerLineWizard(models.TransientModel):
    _name = 'ns.breaker.wizard.line'

    ns_wizard_id = fields.Many2one('ns.space.breaker.wizard')
    ns_wizard_id_selected = fields.Many2one('ns.space.breaker.wizard')
    ns_selected = fields.Boolean('Select', store=True)
    ns_breaker_id = fields.Many2one('ns.ns_breaker', 'Breaker')

class PatchLineWizard(models.TransientModel):
    _name = 'ns.patch.wizard.line'

    ns_wizard_id = fields.Many2one('ns.space.breaker.wizard')
    ns_wizard_id_selected = fields.Many2one('ns.space.breaker.wizard')
    ns_selected = fields.Boolean('Select', store=True)
    ns_patch_id = fields.Many2one('ns.ns_patchpanel', 'Patch Panel')
    
class PortLineWizard(models.TransientModel):
    _name = 'ns.port.wizard.line'

    ns_wizard_id = fields.Many2one('ns.space.breaker.wizard')
    ns_wizard_id_selected = fields.Many2one('ns.space.breaker.wizard')
    ns_selected = fields.Boolean('Select', store=True)
    ns_port_id = fields.Many2one('ns.ns_ports', 'Port')


class SpaceAndBreakerWizard(models.TransientModel):
    _name = 'ns.space.breaker.wizard'

    ns_order_line_id = fields.Many2one('sale.order.line')
    ns_type = fields.Selection([
        ('space', 'Space'),
        ('breaker', 'Breaker'),
        ('patch_panel', 'Patch Panel'),
        ('port', 'Port')
    ], string='type')
    
    ns_space_ids = fields.One2many(comodel_name='ns.space.wizard.line', inverse_name='ns_wizard_id_selected', string='Space')
    ns_space_ids_unselected = fields.One2many(comodel_name='ns.space.wizard.line', inverse_name='ns_wizard_id', string='Space')
    is_search_space = fields.Boolean()
    ns_space_search_ids = fields.Many2many('ns.ns_space', 'wizard_space_rel')
    ns_space_search_helper_ids = fields.Many2many('ns.ns_space', 'wizard_space_helper_rel')
    
    ns_breaker_ids = fields.One2many(comodel_name='ns.breaker.wizard.line', inverse_name='ns_wizard_id_selected', strng='Breaker')
    ns_breaker_ids_unselected = fields.One2many(comodel_name='ns.breaker.wizard.line', inverse_name='ns_wizard_id', string='Breaker')
    is_search_breaker = fields.Boolean()
    ns_breaker_search_ids = fields.Many2many('ns.ns_breaker','wizard_breaker_rel')
    ns_breaker_search_helper_ids = fields.Many2many('ns.ns_breaker','wizard_breaker_helper_rel')
    
    # Patch and Port
    
    ns_patch_ids = fields.One2many(comodel_name='ns.patch.wizard.line', inverse_name='ns_wizard_id_selected', string='Patch')
    ns_patch_ids_unselected = fields.One2many(comodel_name='ns.patch.wizard.line', inverse_name='ns_wizard_id', string='Patch')
    is_search_patch = fields.Boolean()
    ns_patch_search_ids = fields.Many2many('ns.ns_patchpanel', 'wizard_patch_rel')
    ns_patch_search_helper_ids = fields.Many2many('ns.ns_patchpanel', 'wizard_patch_helper_rel')
    
    ns_port_ids = fields.One2many(comodel_name='ns.port.wizard.line', inverse_name='ns_wizard_id_selected', strng='Port')
    ns_port_ids_unselected = fields.One2many(comodel_name='ns.port.wizard.line', inverse_name='ns_wizard_id', string='Port')
    is_search_port = fields.Boolean()
    ns_port_search_ids = fields.Many2many('ns.ns_ports','wizard_port_rel')
    ns_port_search_helper_ids = fields.Many2many('ns.ns_ports','wizard_port_helper_rel')
    
    

    def assign_space_and_breaker(self):
        if self.ns_type == 'space':
            selected = 0
            for space in self.ns_space_ids:
                if space.ns_selected:
                    selected += 1
                    
            for space in self.ns_space_ids_unselected:
                if space.ns_selected:
                    selected += 1
            if selected == int(self.ns_order_line_id.product_uom_qty):
                # for space in self.ns_space_ids:
                for space in self.ns_space_ids:
                    if space.ns_selected:
                        space.ns_space_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserved': True,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'assigned'
                        })
                    else:
                        space.ns_space_id.write({
                            'ns_customer': False,
                            'ns_sale_order_line_id': False,
                            'ns_reserved': False,
                            'ns_reserve_date_until': False,
                            'ns_stage':'avaible'
                        })
                for space in self.ns_space_ids_unselected:
                    if space.ns_selected:
                        space.ns_space_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserved': True,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'assigned'
                        })

            else:
                raise exceptions.ValidationError(_('The selected space quantity is different with the order'))

        if self.ns_type == 'breaker':
            selected = 0
            
            for breaker in self.ns_breaker_ids:
                if breaker.ns_selected:
                    selected += 1

            for breaker in self.ns_breaker_ids_unselected:
                if breaker.ns_selected:
                    selected += 1

            if selected == int(self.ns_order_line_id.product_uom_qty):
                for breaker in self.ns_breaker_ids:
                    if breaker.ns_selected:
                        breaker.ns_breaker_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserved': True,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'assigned'
                        })
                    else:
                        breaker.ns_breaker_id.write({
                            'ns_customer': False,
                            'ns_sale_order_line_id': False,
                            'ns_reserved': False,
                            'ns_reserve_date_until': False,
                            'ns_stage':'avaible'
                        })
                for breaker in self.ns_breaker_ids_unselected:
                    if breaker.ns_selected:
                        breaker.ns_breaker_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserved': True,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'assigned'
                        })
            else:
                raise exceptions.ValidationError(_('The selected breaker quantity is different with the order'))

        if self.ns_type == 'patch_panel':
            selected = 0
            for patch in self.ns_patch_ids:
                if patch.ns_selected:
                    selected += 1
                    
            for patch in self.ns_patch_ids_unselected:
                if patch.ns_selected:
                    selected += 1
            if selected == int(self.ns_order_line_id.product_uom_qty):
                for patch in self.ns_patch_ids:
                    if patch.ns_selected:
                        patch.ns_patch_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'Assigned'
                        })
                    else:
                        patch.ns_patch_id.write({
                            'ns_customer': False,
                            'ns_sale_order_line_id': False,
                            'ns_reserve_date_until': False,
                            'ns_stage':'Available'
                        })
                for patch in self.ns_patch_ids_unselected:
                    if patch.ns_selected:
                        patch.ns_patch_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'Assigned'
                        })

            else:
                raise exceptions.ValidationError(_('The selected patch quantity is different with the order'))

        if self.ns_type == 'port':
            selected = 0
            
            for port in self.ns_port_ids:
                if port.ns_selected:
                    selected += 1

            for port in self.ns_port_ids_unselected:
                if port.ns_selected:
                    selected += 1

            if selected == int(self.ns_order_line_id.product_uom_qty):
                for port in self.ns_port_ids:
                    if port.ns_selected:
                        port.ns_port_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'Assigned'
                        })
                    else:
                        port.ns_port_id.write({
                            'ns_customer': False,
                            'ns_sale_order_line_id': False,
                            'ns_reserve_date_until': False,
                            'ns_stage':'Available'
                        })
                for port in self.ns_port_ids_unselected:
                    if port.ns_selected:
                        port.ns_port_id.write({
                            'ns_customer': self.ns_order_line_id.order_id.partner_id.id,
                            'ns_sale_order_line_id': self.ns_order_line_id.id,
                            'ns_reserve_date_until': fields.Date().today() + timedelta(days=29),
                            'ns_stage':'Assigned'
                        })
            else:
                raise exceptions.ValidationError(_('The selected port quantity is different with the order'))
    
  
    def button_finish_search(self):
        """when finish doing searching user need to click this button"""
        for rec in self:
            if rec.ns_type == 'breaker':
                for breaker in rec.ns_breaker_ids_unselected.filtered(lambda p: p.ns_selected == True):
                    breaker.ns_selected = False
                breakers = rec.ns_breaker_ids_unselected.filtered(lambda p: p.ns_breaker_id.id in rec.ns_breaker_search_ids.ids)
                if not breakers:
                    raise Warning(_('You dont have any breaker selected from the filter'))
                for breaker in breakers:
                    breaker.ns_selected = True
            elif rec.ns_type == 'space':
                for space in rec.ns_space_ids_unselected.filtered(lambda p: p.ns_selected == True):
                    space.ns_selected = False
                spaces = rec.ns_space_ids_unselected.filtered(lambda p: p.ns_space_id.id in rec.ns_space_search_ids.ids)
                if not spaces:
                    raise Warning(_('You dont have any space selected from the filter'))
                for space in spaces:
                    space.ns_selected = True
            elif rec.ns_type == 'patch_panel':
                for patch in rec.ns_breaker_ids_unselected.filtered(lambda p: p.ns_selected == True):
                    patch.ns_selected = False
                patchs = rec.ns_breaker_ids_unselected.filtered(lambda p: p.ns_breaker_id.id in rec.ns_breaker_search_ids.ids)
                if not patchs:
                    raise Warning(_('You dont have any patch selected from the filter'))
                for patch in patchs:
                    patch.ns_selected = True
            elif rec.ns_type == 'port':
                for port in rec.ns_space_ids_unselected.filtered(lambda p: p.ns_selected == True):
                    port.ns_selected = False
                ports = rec.ns_space_ids_unselected.filtered(lambda p: p.ns_space_id.id in rec.ns_space_search_ids.ids)
                if not ports:
                    raise Warning(_('You dont have any port selected from the filter'))
                for port in ports:
                    port.ns_selected = True
            rec.assign_space_and_breaker()
                
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_confirm(self):
        order_line_id = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        for rec in order_line_id:
            product_type = rec.product_id.ns_capacity_assignation
            if product_type != False and product_type == 'space_id':
                reserved_space = self.env['ns.ns_space'].search([('ns_sale_order_line_id', '=', rec.id)])
                for rec2 in reserved_space:
                    rec2.ns_stage = 'sold'
            if product_type != False and product_type == 'breaker_id':
                reserved_breaker = self.env['ns.ns_breaker'].search([('ns_sale_order_line_id', '=', rec.id)])
                for rec3 in reserved_breaker:
                    rec3.ns_stage = 'sold'
        res = super(SaleOrder, self).action_confirm()
        _logger = logging.info(self)
        return res

    def action_cancel(self):
        stage = self.approval_state
        if stage  in ['sale', 'approved', 'done', 'draft']:
            order_line_id = self.env['sale.order.line'].search([('order_id', '=', self.id)])
            for rec in order_line_id:
                product_type = rec.product_id.ns_capacity_assignation
                if product_type != False and product_type == 'space_id':
                    reserved_space = self.env['ns.ns_space'].search([('ns_sale_order_line_id', '=', rec.id)])
                    for rec2 in reserved_space:
                        rec2.ns_stage = 'avaible'
                        rec2.ns_customer = False
                        rec2.ns_sale_order_line_id = False
                        rec2.ns_reserved = False
                        rec2.ns_reserve_date_until = False
                if product_type != False and product_type == 'breaker_id':
                    reserved_breaker = self.env['ns.ns_breaker'].search([('ns_sale_order_line_id', '=', rec.id)])
                    for rec3 in reserved_breaker:
                        rec3.ns_stage = 'avaible'
                        rec3.ns_customer = False
                        rec3.ns_sale_order_line_id = False
                        rec3.ns_reserved = False
                        rec3.ns_reserve_date_until = False
        res = super(SaleOrder, self).action_cancel()
        return res

class ProjectTask(models.Model):
    _inherit = 'project.task'
    

    def write(self, vals):
        stage_id=vals.get('stage_id',False)
        # looking for In Service id
        if stage_id == 34 :
            _logger = logging.info('space')
            space_id = self.env['ns.ns_space'].search([('id', '=', self.x_studio_space_id.id)])
            for rec2 in space_id:
                rec2.ns_stage = 'installed'
            breaker_id = self.env['ns.ns_breaker'].search([('id', '=',self.x_studio_breaker_id.id)])
            for rec3 in breaker_id:
                rec3.ns_stage = 'installed'

        res = super(ProjectTask, self).write(vals)
        return res

    