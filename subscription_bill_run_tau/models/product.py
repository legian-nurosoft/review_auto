# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class ProductTemplate(models.Model):
    _inherit = "product.template"

    ns_merge_ib_task = fields.Boolean(string='Merge IB Task', default=False)
    ns_no_sub_task = fields.Boolean(string='No Subtask', default=False)
    ns_project_id_allow_subtasks = fields.Boolean(string='Allow Subtask', related='project_id.allow_subtasks')