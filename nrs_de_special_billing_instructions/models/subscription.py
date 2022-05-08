# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime

from odoo.exceptions import AccessError, UserError
import logging
_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    ns_special_billing_instruction = fields.Boolean(string="Special Billing Instructions", default=False, track_visibility='onchange', tracking=True)
    ns_special_billing_user_restriction = fields.Boolean(string="User Restriction", compute='_check_user_group')

    ns_temp_sbi = fields.Boolean(compute='_sbi_current_set')
    ns_sbi_changed = fields.Boolean(compute='_sbi_current_set')
    ns_special_billing_instruction_ids = fields.One2many('ns.special.billing.instruction', 'ns_order_id', string='Special Billing Instruction Lines', compute='_sbi_compute', readonly=True)

    # To check later whether or not ns_special_billing_instruction has been changed
    def _sbi_current_set(self):
        self.ns_temp_sbi = self.ns_special_billing_instruction
        self.ns_sbi_changed = False

    def _sbi_compute(self):
        sales_order = self.x_studio_original_sales_order
        self.ns_special_billing_instruction_ids = sales_order.ns_special_billing_instruction_ids
    
    @api.onchange('ns_special_billing_instruction')
    def _update_sbi_changed(self):
        if self.ns_special_billing_instruction != self.ns_temp_sbi:
            self.ns_sbi_changed = True
        else:
            self.ns_sbi_changed = False

    def _check_user_group(self):
        # Check the user have Sale Support privileges
        for record in self:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                record.ns_special_billing_user_restriction = True
            else:
                record.ns_special_billing_user_restriction = False

    '''
    def _prepare_invoice_data(self):
        # Update Special Billing Instruction in Invoices through Subscription
        res = super(SaleSubscription, self)._prepare_invoice_data()

        res['ns_special_billing_instruction'] = self.ns_special_billing_instruction
        if self.ns_special_billing_instruction:
            sbi_res = []
            for line in self.ns_special_billing_instruction_ids:
                sbi_res.append((0, 0, {
                    'ns_period': line.ns_period,
                    'ns_start_date': line.ns_start_date,
                    'ns_end_date': line.ns_end_date,
                    'ns_special_billing_type': line.ns_special_billing_type,
                    'ns_discount': line.ns_discount,
                    'ns_special_billing_type_description': line.ns_special_billing_type_description,
                    'ns_apply_to': line.ns_apply_to,
                    'ns_product_description': line.ns_product_description,
                    'ns_additional_remarks': line.ns_additional_remarks,
                }))
            res['ns_special_billing_instruction_ids'] = sbi_res

        return res
    '''
    # The above will cause Validation Error, this is the workaround, add Special Billing Instructions only after Invoice has been created
    def _recurring_create_invoice(self, automatic=False):
        res = super(SaleSubscription, self)._recurring_create_invoice(automatic)

        for invoice in res:
            subscription = invoice.invoice_line_ids.subscription_id
            if subscription.ns_special_billing_instruction:
                new_vals = {'ns_special_billing_instruction': True}
                sbi = []
                for line in subscription.ns_special_billing_instruction_ids:
                    sbi.append((0, 0, {
                        'ns_period': line.ns_period,
                        'ns_start_date': line.ns_start_date,
                        'ns_end_date': line.ns_end_date,
                        'ns_special_billing_type': line.ns_special_billing_type,
                        'ns_discount': line.ns_discount,
                        'ns_special_billing_type_description': line.ns_special_billing_type_description,
                        'ns_apply_to': line.ns_apply_to,
                        'ns_product_description': line.ns_product_description,
                        'ns_additional_remarks': line.ns_additional_remarks,
                    }))
                new_vals['ns_special_billing_instruction_ids'] = sbi
                invoice.write(new_vals)
        
        return res