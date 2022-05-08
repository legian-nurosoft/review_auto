# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class JobRequisitionStages(models.Model):
    _name = "ns.job.requisition.stage"
    _description = "Job Requisition Stages"
    _rec_name = 'ns_name'
    _order = 'ns_sequence asc, ns_name asc, id desc'

    ns_name = fields.Char('Name')
    ns_active = fields.Boolean('Active')
    ns_color = fields.Integer('Color')
    ns_sequence = fields.Integer('Sequence')
    ns_approver_ids = fields.Many2many('res.users', string='Approver(s)', copy=False)
    ns_template_id = fields.Many2one('mail.template', domain=[('model','=','ns.job.requisition')], string="Mail Template")
    ns_send_email_to_hiring_manager = fields.Boolean(string='Send Email to Hiring Manager')
    ns_send_email_to_approver = fields.Boolean(string='Send Email to Approver')
    ns_is_approval_stage = fields.Boolean(string='Is Approval Stage')
    ns_is_rejected_stage = fields.Boolean(string='Is Reject Stage')
    ns_show_submit_button = fields.Boolean(string='Show Submit Button')
    ns_show_approve_button = fields.Boolean(string='Show Approve Button')
    ns_show_reject_button = fields.Boolean(string='Show Reject Button')

    @api.onchange('ns_show_approve_button')
    def ns_show_approve_button_onchage(self):
        if self.ns_show_approve_button:
            self.ns_approver_ids = [(4,user.id) for user in self.env.ref('nrs_de_job_requisition.ns_group_job_requisition_approver').users]