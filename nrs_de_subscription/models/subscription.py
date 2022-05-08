# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import datetime
from dateutil.relativedelta import relativedelta
import re

from odoo.exceptions import AccessError, UserError
import logging
_logger = logging.getLogger(__name__)

class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    sale_change_order_count = fields.Integer(compute='_compute_change_sale_order_count')

    def _compute_change_sale_order_count(self):
        for rec in self:
            sales = self.env['sale.order'].search([('order_line.subscription_id', '=', rec.id)])
            rec.sale_change_order_count = len(sales.ids)
    
    can_edit_line = fields.Boolean(compute='_compute_can_edit_line')

    def _compute_can_edit_line(self):
        self.can_edit_line = self.env.user.has_group('base.group_system')

    def open_change_orders(self):
        for rec in self:
            sales = self.env['sale.order'].search([('order_line.subscription_id', '=', rec.id)])
            if sales:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "sale.order",
                    "views": [[self.env.ref('sale_subscription.sale_order_view_tree_subscription').id, "tree"],
                              [self.env.ref('sale.view_order_form').id, "form"],
                              [False, "kanban"], [False, "calendar"], [False, "pivot"], [False, "graph"]],
                    "domain": [["id", "in", sales.ids]],
                    "context": {"create": False},
                    "name": _("Sales Orders"),
                }

    def show_upsell_wizard(self):
        operation_site = self.x_studio_original_sales_order.x_studio_operation_site.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.subscription.wizard",
            "views": [[self.env.ref('sale_subscription.wizard_form_view').id, "form"]],
            "context": {"operation_site": operation_site},
            "name": _("Upsell"),
            "target": "new",
        }

    def adjust_billing(self):       
        operation_site = self.x_studio_original_sales_order.x_studio_operation_site.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "adjust.billing.wizard",
            "views": [[self.env.ref('nrs_de_subscription.adjust_order_wizard_form_view').id, "form"]],
            "context": {"operation_site": operation_site},
            "name": _("Adjust Billing"),
            "target": "new",
        }

    def show_change_order_wizard(self):
        operation_site = self.x_studio_original_sales_order.x_studio_operation_site.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "change.subscription.wizard",
            "views": [[self.env.ref('nrs_de_subscription.change_order_wizard_form_view').id, "form"]],
            "context": {"operation_site": operation_site},
            "name": _("Change Order"),
            "target": "new",
        }

    def _get_adjustment_date(self, line):
        name = line.name
        date_start = datetime.date.today()
        try:
            regexp = r"\[(\d{4}-\d{2}-\d{2}) -> (\d{4}-\d{2}-\d{2})\]"
            match = re.search(regexp, name)
            date_start = fields.Date.from_string(match.group(1))
        except Exception:
            _logger.error('_get_adjustment_date: unable to get date start for billing adjustment')
        return date_start

    def _prepare_invoice(self):
        date = self.recurring_next_date
        invoice = super(SaleSubscription, self)._prepare_invoice()
        invoice['date'] = date
        return invoice

    def partial_invoice_line(self, sale_order, option_line, refund=False, date_from=False): 
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        order_line_obj = self.env['sale.order.line']
        ratio, message, period_msg = self._partial_recurring_invoice_ratio(date_from=date_from)
        # ratio, message = self._partial_recurring_invoice_ratio(date_from=date_from)
        if message != "":
            sale_order.message_post(body=message)
        _discount = (1 - ratio) * 100

        temp_price_unit = self.pricelist_id.with_context(uom=option_line.uom_id.id).get_product_price(option_line.product_id, 1, False)
        temp_discount = _discount
        product_in_subscription = False
        product_in_origin_sales_order = False

        for subs_line in self.recurring_invoice_line_ids:
            if subs_line.product_id.id == option_line.product_id.id:
                _logger.info("-product exist in subscription list.")
                temp_price_unit = subs_line.price_unit
                temp_discount = subs_line.discount
                product_in_subscription = True
        
        if not product_in_subscription:
            for origin_line in self.x_studio_original_sales_order.order_line:
                if origin_line.product_id.id == option_line.product_id.id:
                    _logger.info("-product exist in origin sales order line.")
                    temp_price_unit = origin_line.price_unit
                    temp_discount = origin_line.discount
                    product_in_origin_sales_order = True
        
        if not product_in_subscription and not product_in_origin_sales_order:

            product_or_variant_exist = False
            product_category_exist = False

            for item in self.x_studio_original_sales_order.pricelist_id.item_ids:
                
                in_date_range = False
                if item.date_start and item.date_end:
                    in_date_range = item.date_start.date() <= date_from <= item.date_end.date() 
                elif item.date_start:
                    in_date_range = item.date_start.date()  <= date_from
                elif item.date_end:                    
                    in_date_range = date_from <= item.date_end.date() 
                else:
                    in_date_range = True

                if item.applied_on == '0_product_variant' and item.product_id.id == option_line.product_id.id:
                    if item.min_quantity <= option_line.quantity and in_date_range:
                        if item.compute_price == 'fixed' :
                            temp_price_unit = item.fixed_price                        
                            temp_discount = 0
                        elif item.compute_price == 'percentage' and self.x_studio_original_sales_order.pricelist_id.discount_policy == 'without_discount':                        
                            temp_discount = item.percent_price
                        else:
                            temp_discount = 0                   
                        product_or_variant_exist = True

                elif item.applied_on == '1_product' and item.product_tmpl_id.id == option_line.product_id.product_tmpl_id.id:
                    if item.min_quantity <= option_line.quantity and in_date_range:
                        if item.compute_price == 'fixed' :
                            temp_price_unit = item.fixed_price                        
                            temp_discount = 0
                        elif item.compute_price == 'percentage' and self.x_studio_original_sales_order.pricelist_id.discount_policy == 'without_discount':                       
                            temp_discount = item.percent_price
                        else:
                            temp_discount = 0 
                        product_or_variant_exist = True

                elif item.applied_on == '2_product_category' and item.categ_id.id == option_line.product_id.categ_id.id and not product_or_variant_exist:
                    if item.min_quantity <= option_line.quantity and in_date_range:
                        if item.compute_price == 'fixed':
                            temp_price_unit = item.fixed_price                        
                            temp_discount = 0
                        elif item.compute_price == 'percentage' and self.x_studio_original_sales_order.pricelist_id.discount_policy == 'without_discount':                       
                            temp_discount = item.percent_price
                        else:
                            temp_discount = 0  
                        product_category_exist = True
            
            if not product_or_variant_exist and not product_category_exist:
                temp_discount = 0
        
        values = {
            'order_id': sale_order.id,
            'product_id': option_line.product_id.id,
            'subscription_id': self.id,
            'product_uom_qty': option_line.quantity,
            'product_uom': option_line.uom_id.id,
            'discount': temp_discount,
            'price_unit': temp_price_unit,
            'name': option_line.name,
            'ns_product_attribute_value': option_line.ns_product_attribute_value.id,
        }

        if option_line.is_update_subscription :
            is_attr_changed = False
            if option_line.ns_product_attribute_value_origin != option_line.ns_product_attribute_value:
                is_attr_changed = True
            values = {
                'order_id': sale_order.id,
                'product_id': option_line.product_id.id,
                'subscription_id': self.id,
                'product_uom_qty': option_line.quantity,
                'product_uom': option_line.uom_id.id,
                'discount': option_line.discount,
                'price_unit': option_line.unit_price,
                'name': option_line.name,
                # 'name': option_line.name + '\n' + period_msg,
                'tax_id' : option_line.tax_id,
                'ns_product_attribute_value': option_line.ns_product_attribute_value.id,
                'ns_subscription_line_id': option_line.ns_subscription_line_id.id,
                'ns_sub_task_id': option_line.ns_sub_task_id,
                'ns_is_attribute_changed': is_attr_changed,
            }

        return order_line_obj.create(values)

class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    ns_sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line', compute='_compute_sale_order_line')
    ns_sub_task_id = fields.Many2many('project.task', string='Installed Base Service ID',
                                          compute='_compute_project_task', copy=False)

    def _compute_sale_order_line(self):
        for rec in self:
            subscription = rec.analytic_account_id
            subs_order_line = self.env['sale.order.line'].search(
                [('subscription_id', '=', subscription.id), ('product_id', '=', rec.product_id.id)])
            rec.ns_sale_line_id = subs_order_line and subs_order_line[-1] or False

    def _compute_project_task(self):
        for rec in self:
            rec.ns_sub_task_id = False
            related_tasks = self.env['project.task'].search(
                ['|', ('sale_line_id', '=', rec.ns_sale_line_id.id), ('ns_change_order_line_id', '=', 'rec.ns_sale_line_id.id')])
            for related_task in related_tasks:
                if 'installed base' in related_task.project_id.name.lower():
                    rec.ns_sub_task_id += related_task