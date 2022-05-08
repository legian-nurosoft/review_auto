# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging
from odoo.addons.sale_subscription.models.sale_order import SaleOrder as SaleOrderMain
_logger = logging.getLogger(__name__)

def create_subscriptions(self):
    """
    Create subscriptions based on the products' subscription template.

    Create subscriptions based on the templates found on order lines' products. Note that only
    lines not already linked to a subscription are processed; one subscription is created per
    distinct subscription template found.

    :rtype: list(integer)
    :return: ids of newly create subscriptions
    """
    res = []
    for order in self:
        context = dict(self._context)
        context['current_order'] = order.id
        to_create = order._split_subscription_lines()
        # create a subscription for each template with all the necessary lines
        for template in to_create:
            values = order.with_context(context)._prepare_subscription_data(template)
            values['recurring_invoice_line_ids'] = to_create[template]._prepare_subscription_line_data()
            subscription = self.env['sale.subscription'].sudo().create(values)
            subscription.onchange_date_start()
            res.append(subscription.id)
            for line in to_create[template]:
                line.write({'subscription_id': subscription.id})
            subscription.message_post_with_view(
                'mail.message_origin_link', values={'self': subscription, 'origin': order},
                subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
            )
            self.env['sale.subscription.log'].sudo().create({
                'subscription_id': subscription.id,
                'event_date': fields.Date.context_today(self),
                'event_type': '0_creation',
                'amount_signed': subscription.recurring_monthly,
                'recurring_monthly': subscription.recurring_monthly,
                'currency_id': subscription.currency_id.id,
                'category': subscription.stage_category,
                'user_id': order.user_id.id,
                'team_id': order.team_id.id,
            })
    return res


SaleOrderMain.create_subscriptions = create_subscriptions

class SaleOrder(models.Model):
    _inherit = "sale.order"    

    is_not_adjusted = fields.Selection([('not_adjusted', 'Not Adjusted'), ('ready_to_adjust', 'Ready To Adjust'), ('adjusted', 'Adjusted')], 'Upsell Status', default='not_adjusted')
    ns_is_change_order = fields.Boolean(default=False)

    @api.depends('order_line.product_id.project_id')
    def _compute_tasks_ids(self):
        for order in self:
            if order.ns_is_change_order:
                for line in order.order_line:
                    order.tasks_ids += self.env['project.task'].search(
                        ['|', ('id', 'in', line.ns_sub_task_id.ids), ('ns_change_order_line_id', '=', line.id)])
                order.tasks_count = len(order.tasks_ids)
            else:
                super(SaleOrder, self)._compute_tasks_ids()

    def _prepare_subscription_data(self, template):
        values = super(SaleOrder, self)._prepare_subscription_data(template)
        if 'current_order' in self._context:
            values['x_studio_original_sales_order'] = self._context.get('current_order',False)
        return values

    def update_existing_subscriptions(self):
        """
        Update subscriptions already linked to the order by updating or creating lines.
        if order is upsell, only update subscription when button Adjust Billing is clicked.
        if from change order, then rewrite.
        """
        res = []
        product = self._context.get('product')
        if self.ns_is_change_order and self.is_not_adjusted != 'adjusted':
            self.rewrite_existing_subscriptions()
            self.is_not_adjusted = 'adjusted'
        elif self.subscription_management != 'upsell' or self.is_not_adjusted == 'ready_to_adjust':
            deleted_product_ids = None
            for order in self:
                subscriptions = order.order_line.mapped('subscription_id').sudo()
                if subscriptions and order.subscription_management != 'renew':
                    order.subscription_management = 'upsell'
                res.append(subscriptions.ids)
                if order.subscription_management == 'renew':
                    subscriptions.wipe()
                    subscriptions.increment_period(renew=True)
                    subscriptions.payment_term_id = order.payment_term_id
                    subscriptions.set_open()
                    # Some products of the subscription may be missing from the SO: they can be archived or manually removed from the SO.
                    # we delete the recurring line of these subscriptions
                    deleted_product_ids = subscriptions.mapped(
                        'recurring_invoice_line_ids.product_id') - order.order_line.mapped('product_id')

                if product:
                    for subscription in subscriptions:
                        subscription_lines = order.order_line.filtered(lambda l: l.subscription_id == subscription and l.product_id.recurring_invoice)
                        if product:
                            if subscription_lines.product_id.id == product['product_id']:
                                line_values = subscription_lines.with_context(product=product)._update_subscription_line_data(subscription)
                                subscription.write({'recurring_invoice_line_ids': line_values})
                                subscription = self.env["sale.subscription"].search([('id', '=', subscription.id)])
                                #change the adjusted status of the task
                                sub_task = self.env['project.task'].browse(product['sub_task_id'])
                                sub_task.ns_is_adjusted = True
            
            #check if every task in this sale order is already adjusted or not
            self.is_not_adjusted = 'adjusted'
            for line in self.order_line:
                main_task = self.env['project.task'].search([('sale_line_id.id', '=', line.id)])
                for sub_task in main_task.x_studio_sub_tasks:
                    if not sub_task.ns_is_adjusted:
                        self.is_not_adjusted = 'ready_to_adjust'
                if not line.ns_is_adjusted:
                    self.is_not_adjusted = 'ready_to_adjust'

        else:
            self.is_not_adjusted = 'ready_to_adjust'
        return res

    def rewrite_existing_subscriptions(self):
        """
        rewrite subscriptions already linked to the order by updating lines. & update task state if necessary
        """
        for order in self:
            for line in order.order_line:
                if line.ns_subscription_line_id:
                    values = {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        'uom_id': line.product_uom.id,
                        'discount': line.discount,
                        'price_unit': line.price_unit,
                        'ns_product_attribute_value': line.ns_product_attribute_value.id,
                    }
                    line.ns_subscription_line_id.write(values)
                    line.ns_is_adjusted = True
                    if line.ns_is_attribute_changed:
                        for task in line.ns_sub_task_id:
                            values = {
                                'ns_change_order_line_id': line.id,
                            }
                            if task.stage_id.name == 'In Service' and line.ns_is_attribute_changed:
                                stage = task.stage_find(task.project_id.id, [
                                    ('name', '=', 'Pending Change')])
                                values = {
                                    'ns_change_order_line_id': line.id,
                                    'stage_id': stage,
                                }
                            task.write(values)
                    else:
                        for task in line.ns_sub_task_id:
                            values = {
                                'ns_change_order_line_id': line.id,
                            }
                            task.write(values)
    
    def adjust_billing(self):
        sales = self.env['sale.order'].search([('subscription_management', '=', 'upsell'), ('is_not_adjusted', '=', 'ready_to_adjust')])
        if sales:
            for sale in sales:
                for line in sale.order_line:
                    if line.product_id.recurring_invoice:
                        main_task = self.env['project.task'].search([('sale_line_id.id', '=', line.id)])
                        if main_task:
                            for sub_task in main_task.x_studio_sub_tasks:
                                if sub_task.ns_adjustment_date:
                                    if sub_task.ns_adjustment_date == datetime.today().date():
                                        product = {
                                            'product_id' : line.product_id.id,
                                            'sub_task_id' : sub_task.id,
                                        }
                                        sale.with_context(product=product).update_existing_subscriptions()
                        else:
                            if line.ns_adjustment_date:
                                if line.ns_adjustment_date == datetime.now().date():
                                    product = {
                                        'product_id' : line.product_id.id,
                                        'order_line_id' : line.id,
                                    }
                                    sale.with_context(product=product).update_existing_subscriptions()
                    else:
                        if line.ns_adjustment_date:
                            if line.ns_adjustment_date == datetime.now().date():
                                product = {
                                    'product_id' : line.product_id.id,
                                    'order_line_id' : line.id,
                                }
                                sale.with_context(product=product).update_existing_subscriptions()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ns_subscription_line_id = fields.Many2one('sale.subscription.line')
    ns_is_adjusted = fields.Boolean("Adjusted", default=False)
    ns_adjustment_date = fields.Date(string="Adjusment Date")
    ns_is_attribute_changed = fields.Boolean("Attribute Changed", default=False)
    ns_sub_task_id = fields.Many2many('project.task', string='Installed Base Service ID')

    def _get_invoicing_period_today(self):
        name = self.name
        _logger.info("Name :" + name)
        try:
            regexp = r"\[(\d{4}-\d{2}-\d{2}) -> (\d{4}-\d{2}-\d{2})\]"
            match = re.search(regexp, self.name)
            date_start = datetime.date.today()
            date_end = fields.Date.from_string(match.group(2))
            period_msg = _("Invoicing period") + ": [%s -> %s]" % (
                fields.Date.to_string(date_start), fields.Date.to_string(date_end))
            name = self.product_id.name + '\n' + period_msg
            # name = self.product_id.name
        except Exception:
            _logger.error('_get_invoicing_period_today: unable to update new invoicing period for %r - "%s"',
                          self, self.name)
        return name

    def _update_subscription_line_data(self, subscription):
        """Prepare a dictionary of values to add or update lines on a subscription."""
        values = list()
        dict_changes = dict()
        product = self._context.get('product')
        for line in self:
            sub_task = self.env['project.task'].browse(product['sub_task_id'])
            if line.product_id.id == product['product_id'] and not sub_task.ns_is_adjusted:
                name = line._get_invoicing_period_today()
                sub_line = subscription.recurring_invoice_line_ids.filtered(
                    lambda l: (l.product_id, l.uom_id, str(l.price_unit)) == (line.product_id, line.product_uom, str(round(line.price_unit, 2)))
                )
                if sub_line:
                    # We have already a subscription line, we need to modify the product quantity
                    if len(sub_line) > 1:
                        # we are in an ambiguous case
                        # to avoid adding information to a random line, in that case we create a new line
                        # we can simply duplicate an arbitrary line to that effect
                        sub_line[0].copy({'name': name, 'quantity': 1})
                    else:
                        dict_changes.setdefault(sub_line.id, sub_line.quantity)
                        # upsell, we add the product to the existing quantity
                        dict_changes[sub_line.id] += 1
                else:
                    # we create a new line in the subscription: (0, 0, values)
                    subscription_line_data = line._prepare_subscription_line_data()
                    subscription_line_data[0][2].update({'name':name, 'quantity': 1})
                    values.append(subscription_line_data[0])

        values += [(1, sub_id, {'quantity': dict_changes[sub_id]}) for sub_id in dict_changes]
        return values

    def _timesheet_service_generation(self):
        if not self.order_id.ns_is_change_order:
            super(SaleOrderLine, self)._timesheet_service_generation()
        
    # def _prepare_invoice_line(self, vals):
    #     res = super(SaleOrderLine, self)._prepare_invoice_line(vals)
    #     res.update({
    #         'name': res['name'].split('Invoicing period:')[0],
    #         # 'name': 'terserah',
    #     })
    #     return res
