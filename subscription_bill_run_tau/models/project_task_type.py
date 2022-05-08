# -*- coding: utf-8 -*-

from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    x_deprovisioning_stage = fields.Boolean(string="Deprovisioning stage")
