# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AdjustBillingWizard(models.TransientModel):
    _name = 'adjust.billing.wizard'
    _description = 'Adjust Billing Wizard'

    def _default_subscription(self):
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        return subscription

    @api.model
    def _get_items_from_subscription(self):
        line_vals = []
        subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        sales = self.env['sale.order'].search([('order_line.subscription_id', '=', subscription.id), 
                    ('subscription_management', '=', 'upsell'), ('is_not_adjusted', '=', 'ready_to_adjust')])
        if sales:
            for sale in sales:
                for line in sale.order_line:                     
                    if line.product_id.recurring_invoice:
                        main_task = self.env['project.task'].search([('sale_line_id.id', '=', line.id)])
                        if main_task:
                            for sub_task in main_task.x_studio_sub_tasks:
                                if sub_task.stage_id.name == "In Service" and not sub_task.ns_is_adjusted:
                                    _logger.info("mifa1 %s", sale.ns_is_change_order)
                                    change_order_vals = {
                                        'ns_sale_order_id' : sale.id,
                                        'ns_sale_order_line_id': line.id,
                                        'product_id': line.product_id.id,
                                        'ns_sub_task_id': sub_task.id,
                                        'ns_is_mrc': True,
                                    }
                                    line_vals.append((0,0, change_order_vals))
                        elif sale.ns_is_change_order:
                            if not line.ns_is_adjusted:
                                change_order_vals = {
                                    'ns_sale_order_id' : sale.id,
                                    'ns_sale_order_line_id': line.id,
                                    'product_id': line.product_id.id,
                                    'ns_is_mrc': True,
                                }
                                line_vals.append((0,0, change_order_vals))
                    else:
                        if not line.ns_is_adjusted and line.product_id:
                            change_order_vals = {
                                'ns_sale_order_id' : sale.id,
                                'ns_sale_order_line_id': line.id,
                                'product_id': line.product_id.id,
                                'ns_is_mrc': False,
                            }
                            line_vals.append((0,0, change_order_vals))

        return line_vals
    
    subscription_id = fields.Many2one('sale.subscription', string="Subscription", required=True,
                                      default=_default_subscription, ondelete="cascade")
    change_order_lines = fields.One2many('adjust.billing.wizard.line', 'wizard_id', string="Subscription Lines", 
                                        default=_get_items_from_subscription)
    date_from = fields.Date("Adjust Date", default=fields.Date.today,
                            help="The discount applied when creating a sales order will be computed as the ratio between "
                                 "the full invoicing period of the subscription and the period between this date and the "
                                 "next invoicing date.")

    def set_adjustment_date(self):
        for line in self.change_order_lines:
            if line.ns_is_mrc:
                sub_task = self.env['project.task'].browse(line.ns_sub_task_id.id)
                if sub_task:
                    sub_task.ns_adjustment_date = self.date_from
                else: 
                    order_line = self.env['sale.order.line'].browse(line.ns_sale_order_line_id.id)
                    order_line.ns_adjustment_date = self.date_from
            else:
                order_line = self.env['sale.order.line'].browse(line.ns_sale_order_line_id.id)
                order_line.ns_adjustment_date = self.date_from


class AdjustBillingWizardLine(models.TransientModel):
    _name = "adjust.billing.wizard.line"
    _description = 'Adjust Billing Lines Wizard'

    ns_sale_order_line_id = fields.Many2one('sale.order.line', string="Sales Order Line", required=True, ondelete="cascade")
    wizard_id = fields.Many2one('adjust.billing.wizard', ondelete="cascade")
    ns_sale_order_id = fields.Many2one('sale.order', string='Sale Order Line', ondelete="cascade", required=True)
    ns_sub_task_id = fields.Many2one('project.task', ondelete="cascade", string="Installed Base Service ID")
    product_id = fields.Many2one('product.product', ondelete="cascade", required=True)
    ns_is_mrc = fields.Boolean("Recurring Product")

class ProjectTask(models.Model):
    _inherit = "project.task"

    ns_is_adjusted =  fields.Boolean(string='Adjusted', default=False)
    ns_adjustment_date = fields.Date(string="Adjusment Date")
    