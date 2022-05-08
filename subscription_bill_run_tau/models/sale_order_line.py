# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_task = fields.Many2one('project.task', string="Task")
    ns_merge_ib_task = fields.Boolean(string='Merge IB Task', default=False)
    ns_no_sub_task = fields.Boolean(string='No Subtask', default=False)

    @api.onchange('product_template_id')
    def update_merge_ib_and_no_subtask(self):
        self.ns_merge_ib_task = self.product_template_id.ns_merge_ib_task
        self.ns_no_sub_task = self.product_template_id.ns_no_sub_task

    def _timesheet_create_task(self, project):
        # create as many sub tasks as there is qty on that line.
        # the subtask should be created in the subtask project
        # If the qty is negative prevent the creation of the parent task and do not create
        # subtasks
        # Use addapt _timesheet_create_task_prepare_values
        if self.product_uom_qty > 0:
            res = super()._timesheet_create_task(project)
            
            #remove space and breaker from parent
            if res.x_studio_space_id:
                res.x_studio_space_id.ns_sold = False
                res.x_studio_space_id = False
            if res.x_studio_breaker_id:
                res.x_studio_space_id.ns_sold = False
                res.x_studio_space_id = False

            task_qty = self.product_uom_qty
            res.write({'ns_qty': task_qty})
            if not self.ns_no_sub_task:
                task_to_create = 1 if self.ns_merge_ib_task else int(self.product_uom_qty)                
                for i in range(task_to_create):
                    values = self._timesheet_create_task_prepare_values(project)
                    values['parent_id'] = res.id
                    values['sale_order_id'] = False
                    values['ns_qty'] = task_qty
                    if project.allow_subtasks and project.subtask_project_id:
                        values['project_id'] = project.subtask_project_id.id
                    task = self.env['project.task'].sudo().create(values)
                    # task['name'] = "%s" % (task.name)
                    # post message on task
                    task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s)") % (self.order_id.id, self.order_id.name, self.product_id.name)
                    task.message_post(body=task_msg)
            return res

    def _prepare_subscription_line_data(self):
        res = super()._prepare_subscription_line_data()
        self.update_date_to_confirm(self, res)
        return res

    def _update_subscription_line_data(self, subscription):
        res = super()._update_subscription_line_data(subscription)
        self.update_date_to_confirm(self, res)
        return res

    def update_date_to_confirm(self, lines, res):
        for i in range(len(lines)):
            for j in range(len(res)):
                if res[j][2].get('product_id') == lines[i].product_id.id:
                    is_upsell = False
                    if lines[i].product_uom_qty > 0:
                        is_upsell = True

                    res[j][2].update({'x_date_to_confirm': [(0, 0, {
                        'x_isupsell': is_upsell,
                        'x_date_to_confirm': lines[i].order_id.x_date_to_confirm,
                        'x_quantity': abs(lines[i].product_uom_qty),
                        'x_iscounted': False
                    })]})
