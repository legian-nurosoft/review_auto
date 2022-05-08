# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _create_date_range_seq(self, date):
        if 'month_date_range' in self._context:
            date_from = date.replace(day=1)
            date_to = date_from + relativedelta(day=31)
            seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
                'date_from': date_from,
                'date_to': date_to,
                'sequence_id': self.id,
            })
            return seq_date_range
        else:
            return super(IrSequenceDateRange, self)._create_date_range_seq(date)
        