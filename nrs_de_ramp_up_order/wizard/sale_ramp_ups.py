from odoo import models, fields, api


class SaleRampUps(models.TransientModel):
    _name = 'sale.ramp.ups'
    _description = 'Sale Ramp Ups'

    sale_id = fields.Many2one('sale.order')
    ramp_up_to_execute = fields.Many2one('ns.ramp.ups')
    order_line = fields.One2many('sale.ramp.ups.line', 'sale_ramp_id')

    def confirm_ramp_ups(self):
        list_lines_to_subscribe = dict()
        list_lines_nrc = dict()
        order_lines_wo_section_n_note = self.order_line #.filtered(lambda l: l.display_type == False)
        for line in order_lines_wo_section_n_note:
            if line.product_id.subscription_template_id and line.product_id.recurring_invoice and line.product_uom_qty > 0:
                list_lines_to_subscribe[line.sale_line_id] = line.product_uom_qty
            elif not line.product_id.recurring_invoice  and line.product_uom_qty > 0:
                list_lines_nrc[line.sale_line_id] = line.product_uom_qty
        if self.sale_id._origin.state in ('draft','approved', 'sent') and order_lines_wo_section_n_note:
            self.sale_id.with_context(
                from_wizard_sale_ramp_ups=True, 
                list_lines_to_subscribe=list_lines_to_subscribe, 
                list_lines_nrc=list_lines_nrc, 
                start_date_ramp_up=self.ramp_up_to_execute.ns_start_date,
                ramp_up=self.ramp_up_to_execute
            ).action_confirm()
            subscription_id = self.mapped('order_line.sale_line_id.subscription_id')
            if subscription_id:
                self.ramp_up_to_execute.ns_subscription = subscription_id
            self.sale_id.send_notification_to_manager()
        elif self.sale_id.state != 'cancel' and order_lines_wo_section_n_note:
            list_subscription = self.sale_id.with_context(
                list_lines_to_subscribe=list_lines_to_subscribe, 
                list_lines_nrc=list_lines_nrc, 
                without_write_sale_line=True,
                start_date_ramp_up=self.ramp_up_to_execute.ns_start_date,
                ramp_up=self.ramp_up_to_execute
            ).create_subscriptions()
            # end_date_so=self.sale_id.ns_end_date,
            subscription_id = False
            if list_subscription:
                subscription_id = self.env['sale.subscription'].browse(list_subscription[0])

            if subscription_id:
                subscription_id.x_sale_order_ids = self.sale_id
                self.ramp_up_to_execute.ns_subscription = subscription_id

class SaleRampUpsLine(models.TransientModel):
    _name = 'sale.ramp.ups.line'
    _order = 'sale_ramp_id, sequence, id'
    _description = 'Sale Ramp Ups Line'

    sale_ramp_id = fields.Many2one('sale.ramp.ups')
    sale_line_id = fields.Many2one('sale.order.line')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Description')
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    price_unit = fields.Float('Unit Price', digits='Product Price')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    discount = fields.Float(string='Disc.%', digits='Discount')
    currency_id = fields.Many2one(related='sale_ramp_id.sale_id.pricelist_id.currency_id', string='Currency')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', currency_field='currency_id', store=True)
    display_type = fields.Selection([('line_section', "Section"),('line_note', "Note")], default=False, copy=False)
    sequence = fields.Integer(string='Sequence', default=10, copy=False)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.sale_ramp_id.sale_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.sale_ramp_id.sale_id.partner_shipping_id)
            line.update({'price_subtotal': taxes['total_excluded']})
