from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class Subscription(models.Model):
    _inherit = "sale.subscription"

    ns_task_count = fields.Integer('Task Count', compute='_compute_task_count')
    ns_is_can_start = fields.Boolean(compute='_compute_ns_is_can_start', string="Is Can Start", readonly=True)

    def _get_related_task(self):
        related_task = self.env['project.task']
        if self.x_studio_original_sales_order.ns_ramp_ups:
            for ramp_up in self.x_studio_original_sales_order.ns_ramp_ups:
                if self.id == ramp_up.ns_subscription.id:
                    related_task += ramp_up.ns_project_task_id
        else:
            sale_lines = self.env['sale.order.line'].search([('order_id','=',self.x_studio_original_sales_order.id)])
            for line in sale_lines:
                if self.id == line.subscription_id.id:
                    related_task += line.ns_project_task_id

        return related_task

    def _compute_task_count(self):
        for rec in self:
            rec.ns_task_count = len(rec._get_related_task())

    def _compute_ns_is_can_start(self):
        for rec in self:
            can_start = False
            related_tasks = rec._get_related_task()
            for task in related_tasks:
                if "in service" in task.stage_id.name.lower():
                    can_start = True
                    break
            rec.ns_is_can_start = can_start

    def open_related_task(self):
        self.ensure_one()

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self._get_related_task().mapped('project_id')
        if len(task_projects) == 1 and len(self._get_related_task()) > 1:  # redirect to task of the project (with kanban stage, ...)
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self._get_related_task().ids)]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}  # erase default context to avoid default filter
            if len(self._get_related_task()) > 1:  # cross project kanban task
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]
            elif len(self._get_related_task()) == 1:  # single task -> form view
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self._get_related_task().id
        # filter on the task of the current SO
        action.setdefault('context', {})
        return action