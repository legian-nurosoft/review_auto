from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    ns_subscription_count = fields.Integer('MRC Count', compute='_compute_subscription_count')

    def _get_related_subscription(self):
        related_subscription = self.env['sale.subscription']
        if self.sale_line_id.order_id.ns_ramp_ups:
            for ramp_up in self.sale_line_id.order_id.ns_ramp_ups:
                if self.id in ramp_up.ns_project_task_id.ids:
                    related_subscription += ramp_up.ns_subscription

        else:
            related_subscription += self.sale_line_id.subscription_id

        return related_subscription

    def _compute_subscription_count(self):
        for rec in self:
            if rec.parent_id:
                rec.ns_subscription_count = rec.parent_id.ns_subscription_count
            else:
                rec.ns_subscription_count = len(rec._get_related_subscription())

    def open_related_subscription(self):
        self.ensure_one()
        if self.parent_id:
            return self.parent_id.open_related_subscription()
        else:
            subscriptions = self._get_related_subscription()
            action = self.env["ir.actions.actions"]._for_xml_id("sale_subscription.sale_subscription_action")
            if len(subscriptions) > 1:
                action['domain'] = [('id', 'in', subscriptions.ids)]
            elif len(subscriptions) == 1:
                form_view = [(self.env.ref('sale_subscription.sale_subscription_view_form').id, 'form')]
                if 'views' in action:
                    action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
                else:
                    action['views'] = form_view
                action['res_id'] = subscriptions.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            action['context'] = dict(self._context, create=False)
            return action