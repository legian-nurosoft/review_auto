# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class QualificationTag(models.Model):
    _name = "ns.qualification.tag"
    _description = "Qualification Tag"
    _rec_name = 'ns_name'
    _order = 'ns_sequence asc, ns_name asc, id desc'

    ns_name = fields.Char('Name')
    ns_active = fields.Boolean('Active')
    ns_color = fields.Integer('Color')
    ns_sequence = fields.Integer('Sequence')