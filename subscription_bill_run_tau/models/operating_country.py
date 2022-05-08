# -*- coding: utf-8 -*-

from odoo import models, fields


class OperatingCountry(models.Model):
    _name = "operating.country"
    _description = "Operating country"

    name = fields.Char(string="Name")

    x_operation_metros = fields.One2many("operating.metros", "x_operation_country", string="Metros")
    x_sequence = fields.Integer()
