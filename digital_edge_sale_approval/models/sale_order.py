from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    approval_state = fields.Selection([
        ('draft', 'Quotation'),
        ('preapproved', 'To Approve'),
        ('approved', 'Approved'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Approval Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    ns_erp_access_url = fields.Char(string='Erp Access URL', compute='_compute_ns_erp_access_url')
    ns_non_standard_order_line = fields.One2many('sale.order.line', 'order_id', string='Non Standard Order Lines', compute='_compute_ns_non_standard_order_line')
    

    def _compute_ns_non_standard_order_line(self):
        for rec in self:
            non_standard_order_line = self.env['sale.order.line']
            for line in rec.order_line:
                if line.ns_standard_product == 'no' or line.ns_show_custom_attribute_value:
                    non_standard_order_line += line
                elif line.ns_standard_product == 'depend':
                    attr_products = self.env['ns.product.product.attr'].search([('ns_product_id','=', line.product_template_id.id), ('ns_operation_site','=', rec.x_studio_operation_site.id), ('ns_product_attribute_value','=', line.ns_product_attribute_value.id)])
                    if attr_products:
                        if not attr_products.ns_standard:
                            non_standard_order_line += line

            rec.ns_non_standard_order_line = non_standard_order_line    
    
    def _compute_ns_erp_access_url(self):
        for rec in self:
            url = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url', '')
            rec.ns_erp_access_url = 'http://' + url + '/web#model=sale.order&id=%s' % (rec.id)

    def do_submit_quotation(self):
        return self.write({'approval_state': 'preapproved'})

    def action_submit_quotation(self):
        if not self.partner_id.ns_finance_approved:
            raise UserError(_("The Company has not been approved by Finance, please ask your country's Finance Manager to approve"))

        if len(self.ns_non_standard_order_line) > 0:
            for line in self.order_line:
                if line.product_template_id.ns_standard_product == 'depend':
                    attr_products = self.env['ns.product.product.attr'].search([('ns_product_id','=', line.product_template_id.id), ('ns_operation_site','=', self.x_studio_operation_site.id), ('ns_product_attribute_value','=', line.ns_product_attribute_value.id)])
                    if not attr_products:
                        raise exceptions.ValidationError(_('This product-product attribute combination has not been created. Please contact Product Team'))

            return {
                'name': _('Submit Quotation'),
                'view_mode': 'form',
                'res_model': 'sale.order',
                'view_id': self.env.ref('digital_edge_sale_approval.view_order_form_non_standard_wizard').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new'
            }
        else:
            return self.do_submit_quotation()
     
    def do_approve_quotation(self):
        return self.write({'approval_state': 'approved'})   

    def action_approve_quotation(self):
        if len(self.ns_non_standard_order_line) > 0:
            for line in self.order_line:
                if line.product_template_id.ns_standard_product == 'depend':
                    attr_products = self.env['ns.product.product.attr'].search([('ns_product_id','=', line.product_template_id.id), ('ns_operation_site','=', self.x_studio_operation_site.id), ('ns_product_attribute_value','=', line.ns_product_attribute_value.id)])
                    if not attr_products:
                        raise exceptions.ValidationError(_('This product-product attribute combination has not been created. Please contact Product Team'))

            return {
                'name': _('Approve Quotation'),
                'view_mode': 'form',
                'res_model': 'sale.order',
                'view_id': self.env.ref('digital_edge_sale_approval.view_order_form_non_standard_wizard').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new'
            }
        else:
            return self.do_approve_quotation()

    def write(self, values):
        if 'state' in values:
            if self.state == 'draft' and self.approval_state in ['draft', 'preapproved'] and values.get('state') in ['sent', 'sale']:
                raise UserError(_('Cannot change unapproved quotation to sale order'))
            values.update({'approval_state': values.get('state')})

        
        return super().write(values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ns_standard_product = fields.Selection([
            ('yes','Yes'),
            ('no','No'),
            ('depend','Depend')
        ], string='Standard Product', related='product_template_id.ns_standard_product')
    ns_product_attribute = fields.Many2one('product.attribute', string='Product Attribute', related='product_template_id.ns_product_attribute')
    ns_show_custom_attribute_value = fields.Boolean(string='Show Custom Attribute Value', related='product_template_id.ns_show_custom_attribute_value')
    ns_custom_attribute_value = fields.Float(digits='Oppt kVA', string='Custom Attribute Value')
    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Product Attribute', domain="[('attribute_id', '=', ns_product_attribute)]")

    @api.onchange('product_template_id')
    def update_product_attribute_domain(self):
        if self.product_template_id.ns_standard_product == 'no':
            return {'warning': {'title': _('Warning'),'message': _('You have chosen a non-standard product')}}
        if self.product_template_id.ns_standard_product == 'depend':
            allowed_attribute = []
            attr_products = self.env['ns.product.product.attr'].search([('ns_product_id','=', self.product_template_id.id), ('ns_operation_site','=', self.order_id.x_studio_operation_site.id)])
            for attribute in attr_products:
                allowed_attribute.append(attribute.ns_product_attribute_value.id)
            return {
                'domain': {'ns_product_attribute_value': [('id','in',allowed_attribute)]}
            }

    @api.onchange('ns_product_attribute_value')
    def check_product_attribute(self):
        if self.product_template_id:
            if self.product_template_id.ns_standard_product == 'depend':
                attr_products = self.env['ns.product.product.attr'].search([('ns_product_id','=', self.product_template_id.id), ('ns_operation_site','=', self.order_id.x_studio_operation_site.id), ('ns_product_attribute_value','=', self.ns_product_attribute_value.id)])
                if attr_products:
                    for attr in attr_products:
                        if not attr.ns_standard:
                            return {'warning': {'title': _('Warning'),'message': _('You have chosen a non-standard product attribute')}}
                else:
                    return {'warning': {'title': _('Warning'),'message': _('This product-product attribute combination has not been created. Please contact Product Team')}}

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['ns_product_attribute_value'] = self.ns_product_attribute_value.id

        return res
