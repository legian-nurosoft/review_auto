# -*- coding: utf-8 -*-

from odoo import models, api

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_html(self, docids, data=None):
        new_context = dict(self._context)
        if docids:
            if self.model in ['sale.order', 'account.move']:
                obj = self.env[self.model].browse(docids)
                if obj:
                    if obj[0].partner_id.lang:
                        if 'context' in data:
                            data['context']['lang'] = obj[0].partner_id.lang
                        new_context['lang'] = obj[0].partner_id.lang
        
        return super(IrActionsReport, self.with_context(new_context))._render_qweb_html(docids, data=data)

