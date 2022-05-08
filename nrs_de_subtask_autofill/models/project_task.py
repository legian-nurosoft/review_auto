# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_studio_installed_date = fields.Datetime(string='Installed Date')

    def write(self, values):
        if 'stage_id' in values:
            stage=values.get('stage_id')
            if self.env['project.task.type'].browse(stage).name == 'Customer Acceptance':
                if self.allow_subtasks == False:
                    values['x_studio_installed_date'] = datetime.now()
            if self.env['project.task.type'].browse(stage).name == 'In Service':
                values['x_studio_service_commencement_date'] = datetime.now()
        return super(ProjectTask, self).write(values)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_task_prepare_values(self, project):
        res = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        if not self.order_id.ns_is_ramp_up:
            res.update({'x_studio_service_request_date': self.order_id.x_studio_service_request_date})
        return res

    

