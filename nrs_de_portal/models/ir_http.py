# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        mods = super(IrHttp, cls)._get_translation_frontend_modules_name()
        return mods + ['nrs_de_portal']

    @classmethod
    def _authenticate(cls, endpoint):
        res = super(IrHttp, cls)._authenticate(endpoint=endpoint)
        auth_method = endpoint.routing["auth"]
        if auth_method == "user" and request and request.env and request.env.user:
            request.env.user._idle_sessions_check()
        return res
