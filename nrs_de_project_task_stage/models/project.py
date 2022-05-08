# -*- coding: utf-8 -*-

from odoo import models, api, fields, exceptions, _

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    ns_forbid_go_to_previous_stage = fields.Boolean(string='Forbid Go To Previous Stage', default=False)
    ns_forbid_category_id = fields.Many2many('product.category', string='Forbid Product Category', help='Forbid task with specific product category to this stage')
    ns_check_related_space_id = fields.Many2one('project.task.type', string='Check Related Space', help='Forbid task with specific product category to this stage if related task not in this stage')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        if vals.get('stage_id',False) and self.stage_id.ns_forbid_go_to_previous_stage:
            new_stage = self.env['project.task.type'].browse(vals.get('stage_id',False))
            if new_stage:
                if new_stage.sequence < self.stage_id.sequence:
                    raise exceptions.ValidationError(_('You can not move this record to previous stage.'))

        res = super(ProjectTask, self).write(vals)
        if vals.get('stage_id',False) and self.x_studio_product_category.id in self.stage_id.ns_forbid_category_id.ids:
            if not self.x_studio_related_space_service_id or self.x_studio_related_space_service_id.stage_id.name != self.stage_id.ns_check_related_space_id.name:
                raise exceptions.ValidationError(_('Please set the Related Space Service ID, then move it to %s' % (self.stage_id.ns_check_related_space_id.name)))
        return res

    