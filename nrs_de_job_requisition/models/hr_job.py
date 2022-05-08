# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Job(models.Model):
    _inherit = "hr.job"

    ns_job_requisition_id = fields.Many2one('ns.job.requisition', string='Job Requisition')
    ns_hiring_manager_id = fields.Many2one('res.users', string='Hiring Manager', domain="[('share', '=', False)]")
    ns_hiring_managers_manager = fields.Many2one('hr.employee', string='Hiring Manager’s Manager')
    ns_date_of_request = fields.Date('Date of Request')
    ns_type_of_position = fields.Selection([
            ('employee', 'Employee'),
            ('fixed_term_contract_employee', 'Fixed Term Contract Employee'),
            ('independent_consultant', 'Independent Consultant')
        ], string='Type of Position')
    ns_work_location = fields.Selection([
            ('osaka', 'Osaka'),
            ('hong_kong', 'Hong Kong'),
            ('singapore', 'Singapore'),
            ('korea', 'Korea'),
            ('shanghai', 'Shanghai'),
            ('beijing', 'Beijing'),
            ('philippines', 'Philippines'),
            ('usa', 'USA'),
            ('indonesia', 'Indonesia'),
            ('tokyo', 'Tokyo')
        ], string='Work Location')
