# -*- coding: utf-8 -*-

from odoo import models, fields


class dateToConfirm(models.Model):

    _name = "date.confirm"
    _description = "Date To Confirm"

    x_subscription_line = fields.Many2one("sale.subscription.line", string="Subscription Line")
    x_isupsell = fields.Boolean(string="Is upsell")
    x_date_to_confirm = fields.Date(string="Date to Confirm")
    x_quantity = fields.Float(string="Quantity")
    x_iscounted = fields.Boolean(string="Is counted")
