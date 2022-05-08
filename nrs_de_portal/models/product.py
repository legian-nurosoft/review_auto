# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    nrs_color = fields.Char(string='Color')