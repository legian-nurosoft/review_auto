# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.tools import format_date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    recurring_next_date = fields.Date(default=False)
    x_sale_order_ids = fields.One2many('sale.order', string='Sale Order ids', compute="_get_sale_order")
    x_contract_end_date = fields.Date(string="Contract End Date", compute="_compute_contract_end_date")

    # prepare the start and end date of invoice base on invoice start date or next invoice date
    def prepare_date(self):
        invoices = self.env['account.move'].search([('invoice_line_ids.subscription_id', 'in', self.ids)])
        if not invoices:
            start_date = self.date_start
            month = self.recurring_next_date.month - self.date_start.month
            end_date = start_date + relativedelta(months=month, day=31)
        else:
            start_date = self.recurring_next_date + relativedelta(day=1)
            end_date = start_date + relativedelta(day=31)
        return start_date, end_date

    def _prepare_invoice_data(self):
        res = super(SaleSubscription, self)._prepare_invoice_data()
        start_date, end_date = self.prepare_date()

        narration = _("This invoice covers the following period: %s - %s") % (format_date(self.env, start_date), format_date(self.env, end_date))
        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.company_id.invoice_terms:
            narration += '\n' + self.company_id.invoice_terms
        res['narration'] = narration
        res['invoice_date'] = self.recurring_next_date + relativedelta(months=1)
        return res

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        res = super(SaleSubscription, self)._prepare_invoice_line(line, fiscal_position, date_start, date_stop)
        if self.env.context.get('custom_quantity'):
            res.update({'price_unit': self.env.context.get('custom_price_unit'), 'quantity': self.env.context.get('custom_quantity')})
        return res

    def _prepare_multiple_invoice_lines(self, line, fiscal_position, date_start, date_stop):

        invoices = self.env['account.move'].search([('invoice_line_ids.subscription_id', 'in', self.ids)])

        invoice_lines = []
        upsell_subcription_dates = []
        downsell_subscription_dates = []
        quantity = line.quantity
        price_unit = line.price_unit or 0.0

        if line.x_date_to_confirm:
            # get all the upsell first time
            upsell_subcription_dates = line.x_date_to_confirm.filtered(lambda x: x.x_isupsell == True and x.x_iscounted == False)
            # get all the downsell first time
            downsell_subscription_dates = line.x_date_to_confirm.filtered(lambda x: x.x_isupsell == False and x.x_iscounted == False)
            if upsell_subcription_dates:
                quantity = line.quantity - sum(upsell_subcription_dates.mapped('x_quantity'))

        # create line for each first time upsell
        for upsell_subscription_date in upsell_subcription_dates:
            upsell_subscription_date_to_confirm = self.date_start
            custom_quantity = upsell_subscription_date.x_quantity
            if upsell_subscription_date.x_date_to_confirm:
                upsell_subscription_date_to_confirm = upsell_subscription_date.x_date_to_confirm
            else: # special handle for the subscription created from the SO
                if downsell_subscription_dates:
                    custom_quantity = upsell_subscription_date.x_quantity - downsell_subscription_dates.x_quantity
            month_diff = self.recurring_next_date.month - upsell_subscription_date_to_confirm.month
            no_of_days_prorate_month = monthrange(upsell_subscription_date_to_confirm.year, upsell_subscription_date_to_confirm.month)[1]
            # calculate the prorate
            prorate = price_unit * (no_of_days_prorate_month - upsell_subscription_date_to_confirm.day + 1) / no_of_days_prorate_month
            remaining_charge =  price_unit * month_diff
            upsell_subscription_date.x_iscounted = True
            if month_diff:
                # seperate prorate period and normal charge period
                prorate_end_date = upsell_subscription_date_to_confirm + relativedelta(day=31)
                monthly_charge_start_date = upsell_subscription_date_to_confirm + relativedelta(months=1, day=1)
                invoice_lines.append((0, 0, self.with_context(custom_quantity=custom_quantity, custom_price_unit=prorate)._prepare_invoice_line(line, fiscal_position, upsell_subscription_date_to_confirm, prorate_end_date)))
                invoice_lines.append((0, 0, self.with_context(custom_quantity=custom_quantity, custom_price_unit=remaining_charge)._prepare_invoice_line(line, fiscal_position, monthly_charge_start_date, date_stop)))
            else:
                invoice_lines.append((0, 0, self.with_context(custom_quantity=custom_quantity, custom_price_unit=prorate)._prepare_invoice_line(line, fiscal_position, upsell_subscription_date_to_confirm, date_stop)))

        # create line for each first time downsell
        for downsell_subscription_date in downsell_subscription_dates:
            downsell_subscription_date_to_confirm = downsell_subscription_date.x_date_to_confirm
            custom_quantity = downsell_subscription_date.x_quantity
            month_diff = downsell_subscription_date_to_confirm.month - date_start.month if not invoices else 0
            no_of_days_prorate_month = monthrange(downsell_subscription_date_to_confirm.year, downsell_subscription_date_to_confirm.month)[1]
            # calculate the prorate
            prorate = price_unit * downsell_subscription_date_to_confirm.day / no_of_days_prorate_month
            custom_price_unit = prorate + price_unit * month_diff
            downsell_subscription_date.x_iscounted = True
            invoice_lines.append((0, 0, self.with_context(custom_quantity=custom_quantity, custom_price_unit=custom_price_unit)._prepare_invoice_line(line, fiscal_position, date_start, downsell_subscription_date_to_confirm)))

        if quantity > 0:
            if not invoices:
                start_date = self.date_start
                month_diff = self.recurring_next_date.month - start_date.month
                no_of_days_prorate_month = monthrange(start_date.year, start_date.month)[1]
                # calculate the prorate
                prorate = price_unit * (no_of_days_prorate_month - start_date.day + 1) / no_of_days_prorate_month
                remaining_charge =  price_unit * month_diff
                if month_diff:
                    # seperate prorate period and normal charge period
                    prorate_end_date = start_date + relativedelta(day=31)
                    monthly_charge_start_date = start_date + relativedelta(months=1, day=1)
                    invoice_lines.append((0, 0, self.with_context(custom_quantity=quantity, custom_price_unit=prorate)._prepare_invoice_line(line, fiscal_position, date_start, prorate_end_date)))
                    invoice_lines.append((0, 0, self.with_context(custom_quantity=quantity, custom_price_unit=remaining_charge)._prepare_invoice_line(line, fiscal_position, monthly_charge_start_date, date_stop)))
                else:
                    invoice_lines.append((0, 0, self.with_context(custom_quantity=quantity, custom_price_unit=prorate)._prepare_invoice_line(line, fiscal_position, date_start, date_stop)))
            else:
                invoice_lines.append((0, 0, self.with_context(custom_quantity=quantity, custom_price_unit=price_unit)._prepare_invoice_line(line, fiscal_position, date_start, date_stop)))

        return invoice_lines

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        revenue_date_start, revenue_date_stop = self.prepare_date()

        invoice_lines = []
        for line in self.recurring_invoice_line_ids:
            invoice_lines += self._prepare_multiple_invoice_lines(line, fiscal_position, date_start=revenue_date_start, date_stop=revenue_date_stop)

        sale_orders = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)])
        for order in sale_orders:
            for line in order.order_line:
                if not line.product_id.recurring_invoice and line.product_uom_qty != line.qty_invoiced:
                    invoice_lines += [(0, 0, line._prepare_invoice_line())]
        return invoice_lines

    def _get_sale_order(self):
        for rec in self:
            rec.x_sale_order_ids =  self.env['sale.order'].search([('order_line.subscription_id', '=', rec.id)])

    @api.depends('date_start')
    def _compute_contract_end_date(self):
        for rec in self:
            sale_order = rec.env['sale.order'].search([('order_line.subscription_id', 'in', rec.ids)], limit=1)
            if rec.date_start and sale_order:
                rec.x_contract_end_date = rec.date_start + relativedelta(months=sale_order.x_contract_term, days=-1)
            else:
                rec.x_contract_end_date = False

    def start_subscription(self):
        super().start_subscription()
        self.ensure_one()
        if not self.date_start:
            self['date_start'] = fields.Date.context_today(self)
            date_value = (self.date_start.replace(day=1) + timedelta(days=32)).replace(day=1)
            self['recurring_next_date'] = date_value
        elif not self.recurring_next_date:
            date_value = (self.date_start.replace(day=1) + timedelta(days=32)).replace(day=1)
            self['recurring_next_date'] = date_value
        return True

    def _recurring_create_invoice(self, automatic=False):
        res = super()._recurring_create_invoice(automatic)
        customers = res.mapped('partner_id')
        merged_invoices = []
        for customer in customers:
            related_invoices = res.filtered(lambda x: x.partner_id == customer)
            # copy the first invioce
            merged_invoice = related_invoices[0].copy()
            lines = related_invoices.mapped('line_ids')
            # copy the lines to merged invoice
            merged_invoice.write({'line_ids': [(2, id) for id in merged_invoice.line_ids.ids]})
            lines.with_context(tracking_disable=True).write({'move_id': merged_invoice.id})
            merged_invoices.append(merged_invoice)
        res.unlink()
        # modify the narration of the merged invoices
        for invoice in merged_invoices:
            start_date = invoice.invoice_line_ids.filtered(lambda x : x.subscription_start_date).sorted(key=lambda x : x.subscription_start_date)[0].subscription_start_date
            end_date = invoice.invoice_line_ids.filtered(lambda x : x.subscription_end_date).sorted(key=lambda x : x.subscription_end_date, reverse=True)[0].subscription_end_date
            narration = _("This invoice covers the following period: %s - %s") % (format_date(self.env, start_date), format_date(self.env, end_date))
            if self.description:
                narration += '\n' + self.description
            elif self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.company_id.invoice_terms:
                narration += '\n' + self.company_id.invoice_terms
            invoice['narration'] = narration
            invoice['invoice_date'] = self.recurring_next_date - relativedelta(months=1)
        return merged_invoices

    def partial_invoice_line(self, sale_order, option_line, refund=False, date_from=False):
        # Add the task to the sale_order_line being created if it is a downsell line (qty
        # is negative and task is linked)
        res = super().partial_invoice_line(sale_order, option_line, refund, date_from)
        if res.product_uom_qty < 0 and res.task_id:
            res['x_task'] = res.task_id
        return res

    def set_close(self):
        # Get all tasks linked to the sale order and call cancel_sub_task
        res = super().set_close()

        for line in self.x_sale_order_ids:
            if line.tasks_ids:
                line.tasks_ids.cancel_sub_task()
        return res


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    x_date_to_confirm = fields.One2many('date.confirm', 'x_subscription_line', string='Date to Confirm')
