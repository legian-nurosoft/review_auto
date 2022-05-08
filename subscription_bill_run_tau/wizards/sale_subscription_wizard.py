# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = "sale.subscription.wizard"

    def create_sale_order(self):
        res = super(SaleSubscriptionWizard, self).create_sale_order()
        if res.get('res_id'):
            sale_order = self.env['sale.order'].browse(res['res_id'])
            sale_order.x_date_to_confirm = self.date_from
            if self._context.get("active_model", False) == "sale.subscription":
                subs = self.env['sale.subscription'].browse(self._context.get("active_id"))
                orders = self.env['sale.order'].search([('name', 'ilike', subs.code + "-SO")])
                sale_order.name = "%s-SO%s"% (subs.code, len(orders) + 1)

        #Call cancel_sub_task on all the tasks linked to a line with negative qty
        for line in self.option_lines:
            if line.quantity < 0:
                if line.x_task:
                    line.x_task.cancel_sub_task(res['res_id'])
                else:
                    raise UserError(_("You should enter negative quantities for line(s) that have task"))
        return res


class SaleSubscriptionWizardOption(models.TransientModel):
    _inherit = "sale.subscription.wizard.option"

    x_task = fields.Many2one('project.task', string="Task")
