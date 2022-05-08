# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class HRRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    ns_need_approval_from_manager = fields.Boolean(string='Need Approval From Manager', default=False)
    ns_approval_stage = fields.Boolean(string='Approval Stage', default=False)