# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel.messages.pofile
import base64
import copy
import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.models import check_method_name
from odoo.service import db, security
from odoo.addons.web.controllers.main import ensure_db

_logger = logging.getLogger(__name__)

class CustomerPortal(http.Controller):
    # @route(['/web'], type='http', auth="user", website=True)
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        host_url = request.httprequest.host_url
        portal_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_portal_url')
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        erp_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url')

        if portal_domain:
            if portal_domain in host_url:
                return werkzeug.utils.redirect('/web/login?error=access&err_domain=portal')
        # if chuanjun_domain:
        #     if chuanjun_domain in host_url:
        #         return werkzeug.utils.redirect('/web/login?error=access&err_domain=portal')
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except  :
            return werkzeug.utils.redirect('/web/login?error=access')
        
    @http.route(['/','/my','/my/home', '/odoo-tutorials'], type='http', auth="user", website=True)
    def home(self, **kw):

        host_url = request.httprequest.host_url
        portal_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_portal_url')
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        erp_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url')

        if portal_domain and portal_domain in host_url:
            return http.local_redirect('/portal', query=request.params, keep_hash=True)
        elif chuanjun_domain and chuanjun_domain in host_url:
            return http.local_redirect('/portal', query=request.params, keep_hash=True)
        elif erp_domain and erp_domain in host_url:  
            return http.local_redirect('/web', query=request.params, keep_hash=True)
        else:                        
            is_internal_user = request.env.user.has_group('base.group_user')
            if is_internal_user :
                return http.local_redirect('/web', query=request.params, keep_hash=True)
            else:
                return http.local_redirect('/portal', query=request.params, keep_hash=True)
    
    @http.route(['/helpdesk/'], type='http', auth="user", website=True)
    def helpdesk(self, **kw):
        return http.local_redirect('/portal#menu_id=ticket-list-table', query=request.params, keep_hash=True)

    @http.route(['/contactus'], type='http', auth="user", website=True)
    def contactus(self, **kw):
        return http.local_redirect('/portal#menu_id=contact-us', query=request.params, keep_hash=True)