# -*- coding: utf-8 -*-
from odoo import models, api, fields

class ProductBundle(models.Model):
    _name = 'ns.product.bundle'
    _rec_name = 'ns_product_bundle_name'

    ns_product_bundle_name = fields.Char('Product Bundle Name')
    ns_operation_metro = fields.Many2many('operating.metros', string='Operation Metro')
    ns_operation_site = fields.Many2many('operating.sites', string='Operation Site', domain="[('x_operation_metros','in',ns_operation_metro)]")
    
    # Table of Product + product attribute + quantity + unit of measure + price + taxes
    ns_product_list = fields.Many2many('ns.product.bundle.line', string='Product Bundle') 
    
    @api.onchange('ns_operation_site')
    def onchange_ns_product_id(self):
        for rec in self:
            return {'domain': {'ns_product_list': [('ns_product_id.x_studio_available_operation_site','in',rec.ns_operation_site.ids)]}}

class ProductBundleLine(models.Model):
    _name = 'ns.product.bundle.line'
    
    # (Product + Price + UoM) - id - list_price - uom_id
    ns_product_id = fields.Many2one('product.template', string='Product')

    ns_product_attribute_type = fields.Many2one('product.attribute', string='Attribute Type', related='ns_product_id.ns_product_attribute')
    ns_product_attribute_value = fields.Many2one('product.attribute.value', string='Attribute Value')
    ns_quantity = fields.Integer(default=1, string='Qty')
    ns_price = fields.Float(default=0, string='Price')
    ns_product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='ns_product_id.uom_id')
    ns_tax_id = fields.Many2many('account.tax', string='Tax')

    @api.onchange('ns_product_id')
    def onchange_ns_product_id(self):
        for rec in self:
            rec.ns_price = rec.ns_product_id.list_price
    
    def create(self, vals):
        return super(ProductBundleLine, self).create(vals)

class ProductBundleSO(models.Model):
    _inherit = 'sale.order'
    
    # Dropdown Product Bundle
    ns_product_bundle = fields.Many2one('ns.product.bundle', string="Product Bundle")

    @api.onchange('x_studio_operation_metro')
    def onchange_x_studio_operation_site(self):
        for rec in self:
            return {'domain': {'ns_product_bundle': [('ns_operation_metro','=',rec.x_studio_operation_metro.id)]}}
    
    @api.onchange('ns_product_bundle')
    def onchange_ns_product_bundle(self):
        product_bundle = self.ns_product_bundle
        product_bundle_list = self.ns_product_bundle.ns_product_list

        for rec in self:
            new_order_lines = [(5, 0, 0)]

            # Order Lama
            for line in self.order_line:
                if line.display_type == 'line_section':
                    vals={
                        'display_type': 'line_section',
                        'name': line.name,
                    }
                elif line.display_type == 'line_note':
                    vals={
                        'display_type': 'line_note',
                        'name': line.name,
                    }
                else:
                    vals={
                        'product_id' : line.product_id,
                        'name' : line.name,
                        'ns_product_attribute_value' : line.ns_product_attribute_value,
                        'ns_custom_attribute_value' : line.ns_custom_attribute_value,
                        'product_uom_qty' : line.product_uom_qty,
                        'product_uom' : line.product_uom,
                        'price_unit' : line.price_unit,
                        'tax_id' : line.tax_id,
                        'discount' : line.discount,
                        'price_subtotal' : line.price_subtotal,
                        'x_studio_total' : line.x_studio_total,
                    }
                new_order_lines.append((0, 0, vals))
            
            # Order Baru

            for line in product_bundle:
                new_order_lines.append((0, 0, {'display_type': 'line_note','name': product_bundle.ns_product_bundle_name,}))
                for item in product_bundle_list:
                    name = '[' + str(item.ns_product_id.default_code) + '] '+ str(item.ns_product_id.name)
                    vals={
                        'product_id' : item.ns_product_id.product_variant_id,
                        'name' : name,
                        'ns_product_attribute_value' : item.ns_product_attribute_value.id,
                        'ns_custom_attribute_value' : item.ns_product_attribute_value.id,
                        'product_uom_qty' : item.ns_quantity,
                        'product_uom' : item.ns_product_uom,
                        'price_unit' : item.ns_price,
                        'tax_id' : item.ns_tax_id,
                        'discount' : 0,
                        'price_subtotal' : item.ns_quantity * item.ns_price,
                        'x_studio_total' : item.ns_quantity * item.ns_price,
                    }
                    new_order_lines.append((0, 0, vals))
            
            rec.order_line = new_order_lines
