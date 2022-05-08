from odoo import models, fields, api, exceptions, _
import logging

_logger = logging.getLogger(__name__)

class Applicant(models.Model):
    _inherit = 'hr.applicant'

    ns_erp_access_url = fields.Char(string='Erp Access URL', compute='_compute_ns_erp_access_url', readonly=True)

    def _compute_ns_erp_access_url(self):
        for rec in self:
            url = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url', '')
            rec.ns_erp_access_url = 'http://' + url + '/web#model=hr.applicant&id=%s' % (rec.id)
