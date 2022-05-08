# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    ns_mailing_group_id = fields.Many2one(
        'ns.mailing.group', "Mailing Group",
        help='Mailing group the user is member of. Used to compute the members of a Mailing Group through the inverse one2many')
    