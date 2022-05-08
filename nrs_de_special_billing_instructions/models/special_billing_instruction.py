# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta
from odoo.exceptions import UserError

from odoo.tools import OrderedSet

class SpecialBillingInstruction(models.Model):
    _name = 'ns.special.billing.instruction'
    _order = 'ns_order_id'
    _description = 'Special Billing Instructions'

    ns_order_id = fields.Many2one('sale.order', string='Sales Order', track_visibility='onchange', tracking=True)
    ns_period = fields.Integer(string='Period', required=True, track_visibility='onchange', tracking=True)
    ns_start_date = fields.Date(string='Start Date', required=True, track_visibility='onchange', tracking=True)
    ns_end_date = fields.Date(string='End Date', readonly=True, compute='_set_end_date', track_visibility='onchange', tracking=True)
    ns_special_billing_type = fields.Selection([
        ('foc', 'FOC'),
        ('discount', 'Discount'),
        ('others', 'Others')
    ], string='Type', required=True, track_visibility='onchange', tracking=True)
    ns_discount = fields.Float(string='Discount', track_visibility='onchange', tracking=True)
    ns_special_billing_type_description = fields.Char(string='Description', track_visibility='onchange', tracking=True)
    ns_apply_to = fields.Selection([
        ('all_products', 'All Products'),
        ('specific_product', 'Specific Product')
    ], string='Apply To', required=True, track_visibility='onchange', tracking=True)
    ns_product_description = fields.Many2many('product.template', string='Products', domain="[('id', 'in', _ns_product_ids)]", track_visibility='onchange', tracking=True)
    ns_additional_remarks = fields.Text(string='Remarks', track_visibility='onchange', tracking=True)

    _ns_product_ids = fields.Many2many('product.template', compute='_set_product_ids')

    @api.onchange('ns_apply_to')
    def _set_domain(self):
        product_ids = [line.product_id.product_tmpl_id.id for line in self.ns_order_id.order_line] if self.ns_order_id and hasattr(self.ns_order_id, 'order_line') and self.ns_order_id.order_line else []
        return {'domain': {'ns_product_description': [('id', 'in', product_ids)]}}

    def _set_product_ids(self):
        self._ns_product_ids = [(6, 0, [line.product_id.product_tmpl_id.id for line in self.ns_order_id.order_line] if self.ns_order_id and hasattr(self.ns_order_id, 'order_line') and self.ns_order_id.order_line else [])]

    @api.onchange('ns_period', 'ns_start_date')
    def _set_end_date(self):
        for record in self:
            if record.ns_start_date:
                start_datetime = fields.Datetime.from_string(record.ns_start_date)
                end_datetime = start_datetime + timedelta(days=record.ns_period)
                record.ns_end_date = fields.Datetime.to_string(end_datetime)
            else:
                record.ns_end_date = False

    def write(self, vals):
        if 'ns_special_billing_type' in vals:
            if vals['ns_special_billing_type'] != 'discount':
                vals['ns_discount'] = False
            elif vals['ns_special_billing_type'] != 'others':
                vals['ns_special_billing_type_description'] = False
        if 'ns_apply_to' in vals and vals['ns_apply_to'] != 'specific_product':
            vals['ns_product_description'] = False

        return super(SpecialBillingInstruction, self).write(vals)


class SpecialBillingInstructionInvoice(models.Model):
    _name = 'ns.special.billing.instruction.invoice'
    _order = 'ns_move_id'
    _description = 'Special Billing Instructions (Invoice)'

    ns_move_id = fields.Many2one('account.move', string='Invoice', required=True, readonly=True)
    ns_period = fields.Integer(string='Period (Days)', default=False, readonly=True)
    ns_start_date = fields.Date(string='Start Date', default=False, readonly=True)
    ns_end_date = fields.Date(string='End Date', default=False, readonly=True)
    ns_special_billing_type = fields.Selection([
        ('foc', 'FOC'),
        ('discount', 'Discount'),
        ('others', 'Others')
    ], string='Type', default=False, readonly=True)
    ns_discount = fields.Float(string='Discount', default=False, readonly=True)
    ns_special_billing_type_description = fields.Char(string='Description', default=False, readonly=True)
    ns_apply_to = fields.Selection([
        ('all_products', 'All Products'),
        ('specific_product', 'Specific Product')
    ], string='Apply To', default=False, readonly=True)
    ns_product_description = fields.Many2many('product.template', string='Products', default=False, readonly=True)
    ns_additional_remarks = fields.Text(string='Remarks', default=False, readonly=True)

    '''
    def _create(self, vals):
        lel = self.env['account.move'].browse(vals[0]['stored']['ns_move_id'])
        raise UserError(str(lel))
    '''