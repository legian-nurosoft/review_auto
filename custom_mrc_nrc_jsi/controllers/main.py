# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.web.controllers.main import DataSet


class DataSetInherit(DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        if kwargs.get('context',False):
            kwargs['context']['ns_from_ui'] = 1
        if model == 'ns.job.requisition' and method == 'onchange' and len(args) > 3:
            kwargs['context']['field_changed'] = args[2]
        return super(DataSetInherit,self)._call_kw(model, method, args, kwargs)