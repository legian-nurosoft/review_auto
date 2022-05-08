# -*- coding: utf-8 -*-

from odoo import api, models
from odoo import api, fields, models, _

class MailTemplate(models.Model):
    _inherit = "mail.template"

    ns_company_id = fields.Many2one('res.company', 'Company', help="Applied to")