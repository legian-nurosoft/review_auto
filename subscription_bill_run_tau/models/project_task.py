# -*- coding: utf-8 -*-

from odoo import _, models, fields
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = "project.task"
    _description = "Project task"

    ns_qty = fields.Float('Quantity',default=1)

    def cancel_sub_task(self, sale_order_id=False):
        # Put the task in the Deprovisioning stage of the project.
        # In the subtask log a note with a link to the sale order of the downsell
        # Raise error if no stage is defined as such in the project.

        deprovisioning_stage = self.project_id.type_ids.filtered(lambda x: x.x_deprovisioning_stage == True)
        if deprovisioning_stage:
            self.stage_id = deprovisioning_stage.id
            if sale_order_id:
                sale_order = self.env['sale.order'].browse(sale_order_id)
                # post message on task
                task_msg = _("This task has been cancelled from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>") % (sale_order.id, sale_order.name)
                self.message_post(body=task_msg)
        else:
            raise UserError(_("No deprovisioning stage in this project"))

            
