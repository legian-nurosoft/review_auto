# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    journal_type_helper = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ], compute="_compute_journal_type")

    def _compute_journal_type(self):
        for rec in self:
            rec.journal_type_helper = rec.journal_id.type

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_origin = fields.Many2one("sale.order", string="Origin SO", compute="_is_subscription_line", related="subscription_id.x_studio_original_sales_order", readonly=False, store=True, tracking=True)
    # x_origin = fields.Many2one("sale.order", string="Origin SO", readonly=False, store=True, tracking=True)
    x_customer_reference = fields.Char(string="Customer Reference", compute="_is_subscription_line", related="x_origin.client_order_ref", readonly=False, store=True, tracking=True)
    # x_customer_reference = fields.Char(string="Customer Reference", readonly=False, store=True, tracking=True)
    x_operating_sites = fields.Many2one("operating.sites", string="Operating Sites", compute="_is_subscription_line", related="x_origin.x_studio_operation_site", readonly=False, store=True, tracking=True)
    # x_operating_sites = fields.Many2one("operating.sites", string="Operating Sites", readonly=False, store=True, tracking=True)
    subscription_start_date = fields.Date(readonly=False, tracking=True)
    subscription_end_date = fields.Date(readonly=False, tracking=True)

    def _is_subscription_line(self):
        for rec in self:
            sale = False
            if rec.subscription_id:
                domain = ['|', '|', ('x_date_to_confirm', '=', rec.subscription_start_date),
                    ('x_date_to_confirm', '=', rec.subscription_end_date),
                    ('x_date_to_confirm', '=', False)]
                sale = rec.env['sale.order'].search(expression.AND([domain, [('order_line.subscription_id', 'in', rec.subscription_id.ids)]]), limit=1)
                if not sale:
                    if rec.subscription_id.x_studio_original_sales_order:
                        sale = rec.subscription_id.x_studio_original_sales_order
            elif rec.sale_line_ids:
                sale = rec.sale_line_ids[0].order_id
            
            rec.x_customer_reference = sale.client_order_ref if sale else False
            rec.x_origin = sale.id if sale else False
            rec.x_operating_sites = sale.x_studio_operation_site.id if sale else False
    
    def write(self, vals):
        if vals and self.move_id:
            original_rec = self.read()[0]

        res = super(AccountMoveLine, self).write(vals)
        
        if vals and self.move_id:
            change_log = ""
            
            if 'subscription_start_date' in vals:
                if vals['subscription_start_date'] != str(original_rec['subscription_start_date']):
                    change_log += "<li>"+self._fields['subscription_start_date'].string+": "+str(original_rec['subscription_start_date'])+" &#8594; "+str(vals['subscription_start_date'])+"</li>"
            if 'subscription_end_date' in vals:
                if vals['subscription_end_date'] != str(original_rec['subscription_end_date']):
                    change_log += "<li>"+self._fields['subscription_end_date'].string+": "+str(original_rec['subscription_end_date'])+" &#8594; "+str(vals['subscription_end_date'])+"</li>"
            if 'x_origin' in vals:
                if vals['x_origin'] != original_rec['x_origin']:
                    temp_x_origin = self.env['sale.order'].browse(vals['x_origin'])
                    change_log += "<li>"+self._fields['x_origin'].string+": "+str(original_rec['x_origin'][1])+" &#8594; "+str(temp_x_origin.name)+"</li>"
            if 'x_customer_reference' in vals:
                if vals['x_customer_reference'] != original_rec['x_customer_reference']:
                    change_log += "<li>"+self._fields['x_customer_reference'].string+": "+str(original_rec['x_customer_reference'])+" &#8594; "+str(vals['x_customer_reference'])+"</li>"
            if 'x_operating_sites' in vals:
                if vals['x_operating_sites'] != original_rec['x_operating_sites']:
                    temp_x_operating_sites = self.env['operating.sites'].browse(vals['x_operating_sites'])
                    change_log += "<li>"+self._fields['x_operating_sites'].string+": "+str(original_rec['x_operating_sites'][1])+" &#8594; "+str(temp_x_operating_sites.name)+"</li>"

            if change_log != "":
                change_log = "<ul>"+change_log+"</ul>"
                self.move_id.message_post(body="Invoice Line for ("+str(self.id)+")"+str(self.product_id.name_get()[0][1])+" changed:"+change_log)
        return res

    ###In case of compute function doesn't work when creating new invoice(account.move), uncomment this section###
    # @api.model
    # def create(self, vals_list):
    #     res = super(AccountMoveLine, self).create(vals_list)

    #     sale = False
    #     if self.subscription_id:
    #         domain = ['|', '|', ('x_date_to_confirm', '=', self.subscription_start_date),
    #             ('x_date_to_confirm', '=', self.subscription_end_date),
    #             ('x_date_to_confirm', '=', False)]
    #         sale = self.env['sale.order'].search(expression.AND([domain, [('order_line.subscription_id', 'in', self.subscription_id.ids)]]), limit=1)
    #         if not sale:
    #             if self.subscription_id.x_studio_original_sales_order:
    #                 sale = self.subscription_id.x_studio_original_sales_order
    #     elif self.sale_line_ids:
    #         sale = self.sale_line_ids[0].order_id
        
    #     self.x_customer_reference = sale.client_order_ref if sale else False
    #     self.x_origin = sale.id if sale else False
    #     self.x_operating_sites = sale.x_studio_operation_site.id if sale else False

    #     return res
    ######
