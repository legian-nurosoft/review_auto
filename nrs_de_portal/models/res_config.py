# -*- encoding: utf-8 -*-
from odoo import api, fields, models
from ast import literal_eval

class SettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    ns_erp_url = fields.Char(string="Digital Edge ERP Address")
    ns_portal_url = fields.Char(string="Digital Edge Portal Address")
    ns_chuanjun_portal_url = fields.Char(string="Chuanjun Portal Address")

    @api.model
    def get_values(self):
        res = super(SettingsInherit, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(ns_erp_url=get_param('nrs_de_portal.ns_erp_url'))
        res.update(ns_portal_url=get_param('nrs_de_portal.ns_portal_url'))
        res.update(ns_chuanjun_portal_url=get_param('nrs_de_portal.ns_chuanjun_portal_url'))
        return res

    def set_values(self):
        super(SettingsInherit, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('nrs_de_portal.ns_erp_url', self.ns_erp_url)
        set_param('nrs_de_portal.ns_portal_url', self.ns_portal_url)
        set_param('nrs_de_portal.ns_chuanjun_portal_url', self.ns_chuanjun_portal_url)