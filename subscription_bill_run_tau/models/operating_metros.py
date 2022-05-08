# -*- coding: utf-8 -*-

from odoo import models, fields


class OperatingMetros(models.Model):
    _name = "operating.metros"
    _description = "Operating metros"

    name = fields.Char(string="Name")

    x_operation_country = fields.Many2one("operating.country", string="Operation Country")
    x_sequence = fields.Integer()
