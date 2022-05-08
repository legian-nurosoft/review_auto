# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class OperatingCountryInherit(models.Model):
    _inherit = 'operating.country'

    ns_sales_phone = fields.Char("Sales Contact Phone")
    ns_sales_email = fields.Char("Sales Contact Email")
    ns_support_phone = fields.Char("Support Contact Phone")
    ns_support_email = fields.Char("Support Contact Email")
    ns_billing_phone = fields.Char("Billing Contact Phone")
    ns_billing_email = fields.Char("Billing Contact Email")


    