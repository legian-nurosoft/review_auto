# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import re

class OperatingSitesInherit(models.Model):
    _inherit = "operating.sites"

    ns_timezone = fields.Char(string='Timezone (UTC)', default="+00:00")

    @api.onchange('ns_timezone')
    def check_timezone(self):
        time = re.search("^[+-]{1}[0-9]{2}:[0-9]{2}$", self.ns_timezone)
        if not time:
            raise exceptions.UserError('Invalid Timezone, please insert timezone with format +00:00 or -00:00')