# -*- coding: utf-8 -*-

from odoo import models, fields


class OperatingSites(models.Model):
    _name = "operating.sites"
    _description = "Operating sites"

    name = fields.Char(string="Name")

    x_operation_metros = fields.Many2one("operating.metros", string="Metros")
    x_sequence = fields.Integer()
