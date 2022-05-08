# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _
import datetime
from dateutil.relativedelta import relativedelta


class ResUsers(models.Model):
    _inherit = 'res.users'

    ns_home_address = fields.Char(string="Home Address", related='employee_id.ns_home_address', readonly=False, related_sudo=False)
    ns_contact_number = fields.Char(string="Contact Number", related='employee_id.ns_contact_number', readonly=False, related_sudo=False)
    ns_personal_email = fields.Char(string="Personal Email", related='employee_id.ns_personal_email', readonly=False, related_sudo=False)
    is_show_personal_details = fields.Boolean(related='employee_id.is_show_personal_details')
    ns_blood_type = fields.Selection(string='Blood Type', related='employee_id.ns_blood_type', readonly=False, related_sudo=False)
    ns_politic_status = fields.Char(string="Politic Status", related='employee_id.ns_politic_status', readonly=False, related_sudo=False)
    ns_health_status = fields.Selection(string='Health Status', related='employee_id.ns_health_status', readonly=False, related_sudo=False)
    ns_health_details = fields.Char(string="Health Details", related='employee_id.ns_health_details', readonly=False, related_sudo=False)
    ns_hukou_address = fields.Char(string="Hukou Address", related='employee_id.ns_hukou_address', readonly=False, related_sudo=False)
    ns_tax_file_city = fields.Char(string="Tax File City", related='employee_id.ns_tax_file_city', readonly=False, related_sudo=False)
    ns_former_employer = fields.Char(string="Former Employer", related='employee_id.ns_former_employer', readonly=False, related_sudo=False)
    ns_nric_issue_date = fields.Date(string="NRIC Issue Date", related='employee_id.ns_nric_issue_date', readonly=False, related_sudo=False)
    ns_race = fields.Char(string="Race", related='employee_id.ns_race', readonly=False, related_sudo=False)
    ns_age = fields.Integer(string="Age", related='employee_id.ns_age', readonly=True, related_sudo=False)
    ns_children = fields.One2many(string='Children', related='employee_id.ns_children', readonly=False, related_sudo=False)
    ns_contact_relationship = fields.Char(string="Contact Relationship", related='employee_id.ns_contact_relationship', readonly=False, related_sudo=False)
    ns_emergency_phone = fields.Char(string="Contact Number", related='employee_id.ns_emergency_phone', readonly=False, related_sudo=False)
    ns_emergency_email = fields.Char(string="Contact Email", related='employee_id.ns_emergency_email', readonly=False, related_sudo=False)
    ns_fund_contribution = fields.Selection(string='Fund Contribution', related='employee_id.ns_fund_contribution', readonly=False, related_sudo=False)
    ns_basic_pension_number = fields.Char(string="Basic Pension Number", related='employee_id.ns_basic_pension_number', readonly=False, related_sudo=False)
    ns_employment_insurance_number = fields.Char(string="Employment Insurance Certificate Number", related='employee_id.ns_employment_insurance_number', readonly=False, related_sudo=False)
    ns_mpf_entitlement = fields.Char(string="MPF Entitlement", related='employee_id.ns_mpf_entitlement', readonly=False, related_sudo=False)
    ns_mpf_exempted_reason = fields.Char(string="MPF Exempted Reason", related='employee_id.ns_mpf_exempted_reason', readonly=False, related_sudo=False)
    ns_insurance = fields.Char(string="Insurance", related='employee_id.ns_insurance', readonly=False, related_sudo=False)
    ns_healthcare = fields.Char(string="Healthcare", related='employee_id.ns_healthcare', readonly=False, related_sudo=False)

    def write(self, vals):
        if self._context.get('from_my_profile', False):
            return super(ResUsers, self.sudo()).write(vals)
        return super(ResUsers, self).write(vals)

    @api.constrains('ns_children','children')
    def _check_children_count(self):
        for rec in self:
            if rec.children != len(rec.ns_children):
                raise exceptions.ValidationError(_('The children count is not mathced.'))