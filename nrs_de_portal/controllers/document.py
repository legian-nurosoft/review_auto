# -*- coding: utf-8 -*-

import base64
import functools
import json
import logging
import math
import re
import requests

from werkzeug import urls

from odoo import fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from odoo.tools.safe_eval import safe_eval
from datetime import datetime
import pytz
from . import portal_helper


class Document(Controller):

    @route(['/documents/faq'], type='json', auth="user", website=False)
    def get_faq(self, **kw):
        user_guides = []
        faq_groups = []

        guides = request.env['nrs.documents'].sudo().search([('nrs_type','=','user_guide')])
        for guide in guides:
            user_guides.append({
                'title': guide.nrs_title,
                'description': guide.nrs_description,
                'body': guide.nrs_body,
                'url': guide.nrs_download_link,
            })

        f_groups = request.env['nrs.faq.group'].sudo().search([])
        for group in f_groups:
            faqs = []
            for faq in group.nrs_faq_ids:
                faqs.append({
                    'id': str(faq.id),
                    'title': faq.nrs_title,
                    'body': faq.nrs_body
                })

            faq_groups.append({
                'id': str(group.id),
                'name': group.nrs_name,
                'faqs': faqs
            })

        return {
            'user_guides': user_guides,
            'faq_groups': faq_groups
        }


    @route(['/search/documents/faq'], type='json', auth="public", website=False)
    def search_documents_faq(self, **kwargs):
        keyword = '%' + kwargs.get('keyword','') + '%' 
        group_ids = []
        faq_ids = []
        query = """
            SELECT
                g.id AS group_id,
                f.id AS faq_id
            FROM nrs_faq_group g
            JOIN nrs_faq f on f.nrs_faq_group_id = g.id
            WHERE 
                g.nrs_name ilike %s OR
                f.nrs_title ilike %s OR
                f.nrs_body ilike %s
        """
        params = (keyword, keyword, keyword)
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall() 
        for res in result:
            if res['group_id'] not in group_ids:
                group_ids.append(res['group_id'])

            if res['faq_id'] not in faq_ids:
                faq_ids.append(res['faq_id'])

        faq_groups = []

        f_groups = request.env['nrs.faq.group'].sudo().search([('id','in',group_ids)])
        for group in f_groups:
            faqs = []
            for faq in group.nrs_faq_ids:
                if faq.id in faq_ids:
                    faqs.append({
                        'id': str(faq.id),
                        'title': faq.nrs_title,
                        'body': faq.nrs_body
                    })
            if len(faqs) > 0:
                faq_groups.append({
                    'id': str(group.id),
                    'name': group.nrs_name,
                    'faqs': faqs
                })

        return {
            'faq_groups': faq_groups
        }


    @route(['/documents/policies'], type='json', auth="user", website=False)
    def get_policies(self, **kw):
        user_policies = []

        policies = request.env['nrs.documents'].sudo().search([('nrs_type','=','policies')])
        for policy in policies:
            user_policies.append({
                'title': policy.nrs_title,
                'published_date': datetime.strftime(policy.nrs_published_date, '%Y/%m/%d') if policy.nrs_published_date else '',
                'url': policy.nrs_download_link,
            })

        return {
            'user_policies': user_policies
        }

    @route(['/search/documents/policies'], type='json', auth="user", website=False)
    def search_policies(self, **kwargs):
        user_policies = []
        keyword = kwargs.get('keyword','')

        policies = request.env['nrs.documents'].sudo().search([('nrs_type','=','policies'), ('nrs_title','ilike',keyword)])
        for policy in policies:
            user_policies.append({
                'title': policy.nrs_title,
                'published_date': datetime.strftime(policy.nrs_published_date, '%Y/%m/%d') if policy.nrs_published_date else '',
                'url': policy.nrs_download_link,
            })

        return {
            'user_policies': user_policies
        }