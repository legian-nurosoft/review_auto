# -*- coding: utf-8 -*-

import base64
import os
import functools
import json
import logging
import math
import re
import requests
import magic

from werkzeug import urls

from odoo import fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from datetime import datetime
import pytz
import base64

_logger = logging.getLogger(__name__)

from . import portal_helper

compress = functools.partial(re.sub, r'\s', '')

TOTP_SECRET_SIZE = 160


class Portal(Controller):

    @route(['/check/user/type'], type='json', auth="user", website=False)
    def cobacheck(self, **kw):
        user = request.env.user.partner_id.x_studio_individual_type
        data = False
        for res in user:
            if res.x_name == "Primary Access Administrator":
                data = True

        return {'result': data}

   
    @route(['/portal/update-acids'], type='json', auth="user", website=False)
    def update_acids(self, **kw):
        current_cookies = dict(request.httprequest.cookies)
        selected_language = ''
        for language in request.env['res.lang'].sudo().get_available():
            if current_cookies.get('frontend_lang','en_US') == language[0]:
                selected_language = language[2]
        return {'selected_language': selected_language}

    @route(['/user/prepare-2fa'], type='json', auth="user", website=False)
    def prepare_2fa(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'data': {}
        }

        try:
            is_allowed = request.env.user._check_credentials(kwargs.get('to_check',''), request.env)
            secret_bytes_count = TOTP_SECRET_SIZE // 8
            secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
            secret = ' '.join(map(''.join, zip(*[iter(secret)]*4)))
            w = request.env['auth_totp.wizard'].create({
                'user_id': request.env.user.id,
                'secret': secret,
            })

            if w:
                result['data']['id'] = w.id
                result['data']['secret'] = secret
                result['data']['url'] = w.url
                result['data']['qrcode'] =  w.qrcode

        except Exception as e:
            print(e)
            result['status'] = 'restricted'
            result['message'] = _('The password you entered is incorrect. Please try again.')

        return result

    @route(['/user/prepare-2fa-popup'], type='json', auth="user", website=False)
    def prepare_2fa_popup(self, **kwargs):
        result = {
            'id': False,
            'secret': False,
            'url': False,
            'qrcode' : False
        }

        secret_bytes_count = TOTP_SECRET_SIZE // 8
        secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
        secret = ' '.join(map(''.join, zip(*[iter(secret)]*4)))
        display_message = request.env.user.partner_id.nrs_show_2fa_setting_message
        w = request.env['auth_totp.wizard'].create({
            'user_id': request.env.user.id,
            'secret': secret,
        })

        if w:
            result['id'] = w.id
            result['secret'] = secret
            result['url'] = w.url
            result['qrcode'] =  w.qrcode        
            result['display_message'] = display_message        

        return result
    
    @route(['/user/disable-message-2fa-popup'], type='json', auth="user", website=False)
    def disable_message_2fa_popup(self, **kwargs):
        result = {
            'status': 'success',
        }
        request.env.user.partner_id.sudo().write({
            'nrs_show_2fa_setting_message': False
        })

        return result

    @route(['/user/enable-2fa'], type='json', auth="user", website=False)
    def enable_2fa(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Two-factor Authentication has been enabled for your account.'),
            'data': {}
        }

        code = kwargs.get('to_check','')
        wizard = portal_helper.get_default_int_value(kwargs.get('wizard_id',''),'',0)

        try:
            c = int(compress(code))
        except ValueError:
            result['status'] = 'restricted'
            result['message'] = _('The verification code you entered is incorrect. Please try again.')

        if result['status'] == 'allowed':
            wizard_id = request.env['auth_totp.wizard'].browse(wizard)
            if wizard_id:
                if request.env.user._totp_try_setting(wizard_id.secret, c):
                    wizard_id.secret = ''
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('The verification code you entered is incorrect. Please try again.')
            else:
                result['status'] = 'restricted'
                result['message'] = _('The verification failed. Pleae try again')

        return result
    
    @route(['/user/disable-2fa'], type='json', auth="user", website=False)
    def disable_2fa(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Two-factor Authentication has been disabled.'),
            'data': {}
        }

        try:
            is_allowed = request.env.user._check_credentials(kwargs.get('to_check',''), request.env)          
            logins = ', '.join(map(repr, request.env.user.mapped('login')))
            if not (request.env.user == request.env.user or request.env.user._is_admin() or request.env.su):
                return False

            request.env.user.sudo().write({'totp_secret': False})
            request.env.user.flush()
            new_token = request.env.user._compute_session_token(request.session.sid)
            request.session.session_token = new_token
        except Exception as e:
            print(e)
            result['status'] = 'restricted'
            result['message'] = _('The password you entered is incorrect. Please try again.')

        return result

    @route(['/user/delete'], type='json', auth="user", website=False)
    def archive_associated_user(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Your changes have been successfully saved.'),
            'data': {}
        }

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = False
        if partner == request.env.user.partner_id.id:
            result['status'] = 'restricted'
            result['message'] = _('You can not delete yourself')
        elif partner not in request.env.user.partner_id.x_studio_associated_company.ids:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')
        else:
            partner_id = request.env['res.partner'].sudo().browse(partner)
            is_admin = portal_helper.has_access_right(partner_id, 'Primary Access Administrator')

            if is_admin:
                result['status'] = 'restricted'
                result['message'] = _('You can not delete the Primary Access Administrator.')

        if result['status'] == 'allowed':
            rel_user = request.env['res.users'].sudo().search([('partner_id','=',partner_id.id)],limit=1)
            rel_user.sudo().write({'active': False})
            partner_id.sudo().with_context({'from_portal': 1}).write({'active': False})

        return result
    
    @route(['/user/uncheck-policy-agreement'], type='json', auth="user", website=False)
    def archive_associated_user(self, **kwargs):

        if request.session.db and request.session.uid:
            request.session.logout(keep_db=True)

            # partner_id = request.env.user.partner_id.id

            # rel_user = request.env['res.users'].sudo().search([('partner_id','=',partner_id)],limit=1)
            # rel_user.sudo().write({'active': False})
            # partner_id.sudo().with_context({'from_portal': 1}).write({'active': False})

        return True

    @route(['/user/activate'], type='json', auth="user", website=False)
    def unarchive_associated_user(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Your changes have been successfully saved.'),
            'data': {}
        }

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = False

        cur_user_id = request.env['res.partner'].sudo().browse(request.env.user.sudo().partner_id.id)
        cur_user_associated = cur_user_id.with_context(active_test=False).x_studio_associated_company._ids

        if partner not in cur_user_associated:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')
        else:
            partner_id = request.env['res.partner'].sudo().browse(partner)

        if result['status'] == 'allowed':
            rel_user = request.env['res.users'].sudo().search([('partner_id','=',partner_id.id)],limit=1)
            rel_user.sudo().write({'active': True})
            partner_id.sudo().with_context({'from_portal': 1}).write({'active': True})

        return result

    @route(['/user/save-associated'], type='json', auth="user", website=False)
    def save_associated_user(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Your changes have been successfully saved.'),
            'data': {}
        }

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')

        access_right = {
            'admin': ['Primary Access Administrator',False],
            'remote-hands': ['Remote Hands',False],
            'ordering': ['Ordering',False],
            'provisioning': ['Provisioning',False],
            'invoicing': ['Invoicing',False],
            'fault-report': ['Fault Report',False],
            'site-access-ticket': ['Site Access Ticket',False],
            'shipment-ticket': ['Shipment Ticket',False]
        }

        if result['status'] == 'allowed':  
            for a_right in access_right:
                is_exist = request.env['x_individual_type'].sudo().search([('x_name','=',access_right[a_right][0])],limit=1)
                if is_exist:
                    access_right[a_right][1] = is_exist.id
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('User "%s" not found.' % (access_right[a_right][0]))

        partners = kwargs.get('associated_company',[])
        if result['status'] == 'allowed':
            for partner in partners:
                if partner['partner_id'] in request.env.user.partner_id.x_studio_associated_company.ids:
                    partner_id = request.env['res.partner'].sudo().browse(partner['partner_id'])
                    individual_type = []
                    for a_right in access_right:
                        if partner[a_right]:
                            individual_type.append(access_right[a_right][1])
                    
                    partner_id.sudo().write({
                            'x_studio_individual_type': [[6,False,individual_type]]
                        })
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('You do not have permission to complete this action.')

        return result

    @route(['/user/associated'], type='json', auth="user", website=False)
    def get_associated_user(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'data': {}
        }

        search_term = kwargs.get('search_term',False)
        show_inactive = kwargs.get('show_inactive',False)

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to access this menu.')

        if result['status'] == 'allowed':
            associated_company = []

            search_domain = []

            cur_user_id = request.env['res.partner'].sudo().browse(request.env.user.sudo().partner_id.id)
            cur_user_associated = cur_user_id.with_context(active_test=False).x_studio_associated_company._ids

            # _logger.info(cur_user_id)
            # _logger.info(">>>>>>>>>>>>> associated_ids .with_context(active_test=False)")
            # _logger.info(cur_user_id.with_context(active_test=False).x_studio_associated_company._ids)
            # _logger.info(">>>>>>>>>>>>> associated_ids no context")
            # _logger.info(cur_user_id.x_studio_associated_company)

            search_domain.append(('id', 'in', cur_user_associated))
            if show_inactive:
                search_domain = expression.AND([search_domain,[('active', '=', False)]])
            else:
                search_domain = expression.AND([search_domain,[('active', '=', True)]])

            if search_term != False:
                for search_data in search_term.split('|'):
                    column = search_data.split('->')[0]
                    value = search_data.split('->')[1]

                    arrayValue = value.split(' or ')

                    if column in ["name", "function", "parent_id.name"]:
                        if len(arrayValue) > 1:
                            temp_domain = False
                            for val in arrayValue:
                                if temp_domain:
                                    temp_domain = expression.OR([temp_domain,[(column, 'ilike', val)]])
                                else:
                                    temp_domain = [(column, 'ilike', val)]
                            search_domain = expression.AND([search_domain,temp_domain])
                        else:
                            search_domain = expression.AND([search_domain,[(column, 'ilike', value)]])
                    elif column in ["x_studio_associated_company"]:
                        if len(arrayValue) > 1:
                            temp_domain = False
                            list_associated_company = ()
                            for val in arrayValue:
                                temp_company = request.env['res.partner'].sudo().search([('name', 'ilike', val)])._ids
                                list_associated_company = list_associated_company + temp_company
                            search_domain = expression.AND([search_domain,[(column, 'in', list_associated_company)]])
                        else:
                            search_domain = expression.AND([search_domain,[(column, 'in', request.env['res.partner'].sudo().search([('name', 'ilike', value)])._ids)]])

            user_associated_company = request.env['res.partner'].sudo().with_context(active_test=False).search(search_domain)
            # for a_com in request.env.user.sudo().partner_id.x_studio_associated_company:
            for a_com in user_associated_company:
                if a_com.nrs_company_type == 'person':
                    associated = []
                    for a_company in a_com.x_studio_associated_company:
                        associated.append(a_company.name)

                    permanent_site_access = []
                    for site in a_com.x_studio_permanent_site_access:
                        permanent_site_access.append(site.name)

                    associated_company.append({
                        'partner_id': a_com.id,
                        'user_name': a_com.name,
                        'user_photo': '/portal/partner_image/%s?unique=%s' % (a_com.id,datetime.strftime(datetime.now(),'%H%m%s')) if a_com.image_1920 else '/nrs_de_portal/static/src/img/user.svg',
                        'company_name': a_com.parent_id.name or '',
                        'user_email': a_com.email or '',
                        'user_position': a_com.function or '',
                        'admin': portal_helper.has_access_right(a_com, 'Primary Access Administrator'),
                        'remote-hands': portal_helper.has_access_right(a_com, 'Remote Hands'),
                        'ordering': portal_helper.has_access_right(a_com, 'Ordering'),
                        'provisioning': portal_helper.has_access_right(a_com, 'Provisioning'),
                        'invoicing': portal_helper.has_access_right(a_com, 'Invoicing'),
                        'fault-report': portal_helper.has_access_right(a_com, 'Fault Report'),
                        'site-access-ticket': portal_helper.has_access_right(a_com, 'Site Access Ticket'),
                        'shipment-ticket': portal_helper.has_access_right(a_com, 'Shipment Ticket'),
                        'active_user': True if a_com.id == request.env.user.partner_id.id else False,
                        'parent_company': a_com.parent_id.name if a_com.parent_id else '',
                        'associated': associated,
                        'pin_code': a_com.x_studio_pin_code or '',
                        'permanent_site_access': permanent_site_access,
                        'mobile': a_com.mobile or '',
                        'phone': a_com.phone or '',
                        'is_privacy_policy_agreement': a_com.nrs_privacy_policy_agreement,
                        # 'id_type': a_com.x_studio_id_type or '',
                        # 'id_number': a_com.x_studio_id_number or '', 
                    })
                # else:
                #     associated_company.append({
                #         'partner_id': a_com.id,
                #         'user_name': a_com.name,
                #         'user_photo': '/portal/partner_image/%s?unique=%s' % (a_com.id,datetime.strftime(datetime.now(),'%H%m%s')) if a_com.image_1920 else '/nrs_de_portal/static/src/img/user.svg',
                #         'company_name': a_com.parent_id.name or '',
                #         'user_email': a_com.email or '',
                #         'user_position': a_com.function or '',
                #         'admin': portal_helper.has_access_right(a_com, 'Primary Access Administrator'),
                #         'remote-hands': portal_helper.has_access_right(a_com, 'Remote Hands'),
                #         'ordering': portal_helper.has_access_right(a_com, 'Ordering'),
                #         'provisioning': portal_helper.has_access_right(a_com, 'Provisioning'),
                #         'invoicing': portal_helper.has_access_right(a_com, 'Invoicing'),
                #         'fault-report': portal_helper.has_access_right(a_com, 'Fault Report'),
                #         'site-access-ticket': portal_helper.has_access_right(a_com, 'Site Access Ticket'),
                #         'shipment-ticket': portal_helper.has_access_right(a_com, 'Shipment Ticket'),
                #         'active_user': True if a_com.id == request.env.user.partner_id.id else False,
                #         'parent_company': a_com.parent_id.name if a_com.parent_id else '',
                #         'associated': [],
                #         'pin_code': a_com.x_studio_pin_code or '',
                #         'permanent_site_access': [],
                #         'mobile': a_com.mobile or '',
                #         'phone': a_com.phone or '', 
                #         'id_type': a_com.x_studio_id_type or '',
                #         'id_number': a_com.x_studio_id_number or '', 
                #     })

            result['data']['associated_company'] = associated_company

        return result

    @route(['/user/save-edit'], type='json', auth="user", website=False)
    def save_user_edit(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': _('Your profile has been updated successfully.'),
            'data': {}
        }

        values = {}

        same_user = kwargs.get('same_user',0)

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        if partner != request.env.user.partner_id.id:
            is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
            if not is_admin:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to complete this action.')

        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        if partner_id:
            if partner_id.id != request.env.user.partner_id.id:
                if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    result['status'] = 'restricted'
                    result['message'] = _('You do not have permission to complete this action.')

        else:
            result['status'] = 'restricted'
            result['message'] = _('User not found.')

        
        if partner_id.id != request.env.user.partner_id.id:
            if len(kwargs.get('companies',[])) <= 0:
                result['status'] = 'restricted'
                result['message'] = _('Associated Entities is a required field. Please enter your Associated Entities')
            else:
                values['x_studio_associated_company'] = [[6,False,kwargs.get('companies',[])]]

            # if len(kwargs.get('sites',[])) <= 0:
            #     result['status'] = 'restricted'
            #     result['message'] = _('Please insert the Permanent Site Access')
            # else:
            #     values['x_studio_permanent_site_access'] = [[6,False,kwargs.get('sites',[])]]
        
        if result['status'] == 'allowed':
            name = kwargs.get('user_name','')
            if len(name) > 0:
                values['name'] = name
            else:
                result['status'] = 'restricted'
                result['message'] = _('Name is a required field. Please enter your Name.')

        if result['status'] == 'allowed':
            parent_id = portal_helper.get_default_int_value(kwargs.get('parent_id',''),'',0)
            if same_user == 0:
                if parent_id > 0:
                    values['parent_id'] = parent_id
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('Company is a required field. Please enter your Comany.')

        if len(kwargs.get('new','')) > 0 or len(kwargs.get('confirm','')) > 0:
            if kwargs.get('new','') != kwargs.get('confirm',''):
                result['status'] = 'restricted'
                result['message'] = _('The value of New Password and Confirm Password is Passwords do not match.')
            else:
                try:
                    if partner_id.id == request.env.user.partner_id.id:
                        is_allowed = request.env.user._check_credentials(kwargs.get('current',''), request.env)
                        request.env.user.sudo().write({'password': kwargs.get('new','')})
                        result['message'] = _('Password Reset Successful')
                        result['data']['need_login'] = True                    
                except Exception as e:
                    result['status'] = 'restricted'
                    result['message'] = _('The password you entered is incorrect. Please try again.')

        if len(kwargs.get('image','')) > 0:
            image = kwargs.get('image','')
            f = magic.Magic(mime=True)
            nime_type = f.from_buffer(base64.b64decode(image))
            list_nime = [
                'image/png',
                'image/jpeg',
                'image/bmp',
                ]
            if nime_type not in list_nime:
                result['status'] = 'restricted'
                result['message'] = _("Your file extension not allowed for upload")
            else:
                values['image_1920'] =image

        if result['status'] == 'allowed':

            if len(kwargs.get('job_position','')) > 0:
                values['function'] = kwargs.get('job_position','')

            if len(kwargs.get('mobile','')) > 0:
                values['mobile'] = kwargs.get('mobile','')

            if len(kwargs.get('phone','')) > 0:
                values['phone'] = kwargs.get('phone','')

            if same_user == 1:
                if len(kwargs.get('pin_code','')) > 0:
                    values['x_studio_pin_code'] = kwargs.get('pin_code','')
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('Please insert pin code')

            # if len(kwargs.get('id_type','')) > 0:
            #     values['x_studio_id_type'] = kwargs.get('id_type','')

            # if len(kwargs.get('id_number','')) > 0:
            #     values['x_studio_id_number'] = kwargs.get('id_number','')
            
            if len(kwargs.get('user_name','')) > 0:
                values['name'] = kwargs.get('user_name','')


            partner_id.sudo().write(values)

            if partner_id.id == request.env.user.partner_id.id:
                result['data']['same_user'] = True
                result['message'] = _('Your profile has been updated successfully.'),
            else:
                result['data']['same_user'] = False                
                result['message'] = _('The data has been updated'),

        return result

    @route(['/user/prepare-edit'], type='json', auth="user", website=False)
    def prepare_user_info_for_edit(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'data': {}
        }

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        if partner != request.env.user.partner_id.id:
            is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
            if not is_admin:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to complete this action.')

        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        if partner_id:
            if partner_id.id != request.env.user.partner_id.id:
                if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    result['status'] = 'restricted'
                    result['message'] = _("You do not have permission to complete this action.")
        else:
            result['status'] = 'restricted'
            result['message'] = _('User not found.')


        if result['status'] == 'allowed':
            associated_company = []
            company_list = []
            for a_com in partner_id.x_studio_associated_company:
                if a_com.nrs_company_type != "person":
                    associated_company.append({'id': a_com.id, 'name': a_com.name})

            for a_com in request.env.user.partner_id.x_studio_associated_company:
                if a_com.nrs_company_type != "person":
                    company_list.append({
                        'id': a_com.id, 
                        'name': a_com.name,
                        'selected': 1 if a_com.id in partner_id.x_studio_associated_company.ids else 0
                    })


            permanent_site_access = []
            site_list = []
            for site in partner_id.x_studio_permanent_site_access:
                permanent_site_access.append({'id': site.id, 'name': site.name})

            for site in request.env.user.partner_id.x_studio_permanent_site_access:
                site_list.append({
                    'id': site.id, 
                    'name': site.name,
                    'selected': 1 if site.id in partner_id.x_studio_permanent_site_access.ids else 0
                })

            # id_type_list = [
            #     {'name': 'Passport', 'selected': True if partner_id.x_studio_id_type == 'Passport' else False},
            #     {'name': 'National ID Card', 'selected': True if partner_id.x_studio_id_type == 'National ID Card' else False},
            #     {'name': 'Driving License', 'selected': True if partner_id.x_studio_id_type == 'Driving License' else False},
            #     {'name': 'Others', 'selected': True if partner_id.x_studio_id_type == 'Others' else False}
            # ]

            result['data'] = {
                'partner_id': partner_id.id,
                'user_name': partner_id.name,
                'user_photo': '/portal/partner_image/%s?unique=%s' % (partner_id.id,datetime.strftime(datetime.now(),'%H%m%s')) if partner_id.image_1920 else '/nrs_de_portal/static/src/img/user.svg',
                'company_name': partner_id.parent_id.name or '',
                'company_id': partner_id.parent_id.id or '',
                'user_email': partner_id.email or '',
                'user_position': partner_id.function or '',
                'associated_company': associated_company,
                'company_list': company_list,
                'same_user': 1 if partner_id.id == request.env.user.partner_id.id else 0,
                'pin_code': partner_id.x_studio_pin_code or '',
                'mobile': partner_id.mobile or '',
                'phone': partner_id.phone or '', 
                # 'id_type': partner_id.x_studio_id_type or '',
                # 'id_number': partner_id.x_studio_id_number or '', 
                'permanent_site_access': permanent_site_access,
                'site_list': site_list,
                'is_privacy_policy_agreement': partner_id.nrs_privacy_policy_agreement
                # 'id_type_list': id_type_list
            }


        return result

    @route(['/user/prepare-add'], type='json', auth="user", website=False)
    def prepare_user_info_for_add(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'data': {}
        }

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You do not have permission to complete this action.')

        if result['status'] == 'allowed':
            partner_id = request.env.user.partner_id
            associated_company = []
            for a_com in partner_id.x_studio_associated_company:
                if a_com.nrs_company_type != "person":
                    associated_company.append({
                        'id': a_com.id,
                        'name': a_com.name
                    })

            site_list = []
            for site in request.env.user.partner_id.x_studio_permanent_site_access:
                site_list.append({
                    'id': site.id, 
                    'name': site.name
                })

            result['data'] = {
                'user_photo': '/nrs_de_portal/static/src/img/user.svg',
                'company_name': partner_id.parent_id.name or '',
                'associated_company': [],
                'company_list': associated_company,
                'site_list': site_list
            }


        return result

    @route(['/user/save-add'], type='json', auth="user", website=False)
    def save_user_add(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
        }

        values = {
            'is_company': False,
            'nrs_company_type': 'person'
        }

        values['x_studio_associated_company'] = [[6,False,kwargs.get('companies',[])]]
        values['x_studio_permanent_site_access'] = [[6,False,kwargs.get('sites',[])]]

        is_admin = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        if not is_admin:
            result['status'] = 'restricted'
            result['message'] = _('You can not add a new user')

        if len(kwargs.get('companies',[])) <= 0:
            result['status'] = 'restricted'
            result['message'] = _('Associated Entities is a required field. Please enter your Associated Entities')

        # is_permanent_site_filled = True
        # if len(kwargs.get('sites',[])) <= 0:
        #     is_permanent_site_filled = False
            # result['status'] = 'restricted'
            # result['message'] = _('Please insert the Permanent Site Access')

        if result['status'] == 'allowed':
            name = kwargs.get('name','')
            if len(name) > 0:
                values['name'] = kwargs.get('name','')
            else:
                result['status'] = 'restricted'
                result['message'] = _('Name is a required field. Please enter your Name.')

        if result['status'] == 'allowed':
            parent_id = portal_helper.get_default_int_value(kwargs.get('parent_id',''),'',0)
            if parent_id > 0:
                values['parent_id'] = parent_id
            else:
                result['status'] = 'restricted'
                result['message'] = _('Company is a required field. Please enter your Comany.')

        if result['status'] == 'allowed':
            email = kwargs.get('email','')
            if len(email) > 0:
                is_exist = request.env['res.partner'].sudo().search([('email','=',email)])
                if is_exist:
                    result['status'] = 'restricted'
                    result['message'] = _('The email address you entered is already taken.')
                else:
                    values['email'] = kwargs.get('email','')
            else:
                result['status'] = 'restricted'
                result['message'] = _('Email is a required field. Please enter your Email.')

        if result['status'] == 'allowed':
            job_position = kwargs.get('job_position','')
            if len(job_position) > 0:
                values['function'] = kwargs.get('job_position','')


            mobile = kwargs.get('mobile','')
            if len(mobile) > 0:
                values['mobile'] = kwargs.get('mobile','')

            phone = kwargs.get('phone','')
            if len(phone) > 0:
                values['phone'] = kwargs.get('phone','')

            pin_code = kwargs.get('pin_code','')
            if len(pin_code) > 0:
                values['x_studio_pin_code'] = kwargs.get('pin_code','')
            else:
                result['status'] = 'restricted'
                result['message'] = _('Please insert pin code')

        if result['status'] == 'allowed':            
            values['nrs_show_2fa_setting_message'] = True
            new_partner = request.env['res.partner'].sudo().create(values)
            request.env.user.partner_id.write({
                'x_studio_associated_company': [[4,new_partner.id]]
            })

            wizard = request.env['portal.wizard'].sudo().create({})
            wizard_user = request.env['portal.wizard.user'].sudo().create({
                'partner_id': new_partner.id,
                'email': new_partner.email,
                'in_portal': True,
                'wizard_id': wizard.id
            })
            
            wizard_user.sudo().with_context({'nrs_skip_email':1}).action_apply()
            user = request.env['res.users'].sudo().search([('partner_id','=',new_partner.id)],limit=1)
            user.with_context({'create_user':1}).action_reset_password();

        return result
            
    @route(['/user'], type='json', auth="user", website=False)
    def get_user_info(self, **kw):
        permanent_site_access = []
        for site in request.env.user.partner_id.x_studio_permanent_site_access:
            permanent_site_access.append(site.name)        
        data = {
            'partner_id': request.env.user.partner_id.id,
            'user_name': request.env.user.partner_id.name,
            'user_photo': '/portal/partner_image/%s?unique=%s' % (request.env.user.partner_id.id,datetime.strftime(datetime.now(),'%H%m%s')) if request.env.user.partner_id.image_1920 else '/nrs_de_portal/static/src/img/user.svg',
            'company_name': request.env.user.partner_id.parent_id.name or '',
            'user_email': request.env.user.partner_id.email or '',
            'user_position': request.env.user.partner_id.function or '',
            'is_admin': portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator'),
            'pin_code': request.env.user.partner_id.x_studio_pin_code or '',
            'permanent_site_access': permanent_site_access,
            'mobile': request.env.user.partner_id.mobile or '',
            'phone': request.env.user.partner_id.phone or '', 
            # 'id_type': request.env.user.partner_id.x_studio_id_type or '',
            # 'id_number': request.env.user.partner_id.x_studio_id_number or '',
            'same_user': 1,
            'is_2fa_enabled': request.env.user.totp_enabled,
            'is_privacy_policy_agreement': request.env.user.partner_id.nrs_privacy_policy_agreement,
        }

        return data

    @route(['/user/route'], type='json', auth="user", website=False)
    def get_user_route(self, **kw):
        route = {
            'dashboard': {
                'title': 'Dashboard',
                'breadcumb': [
                    _('HOME'),
                    _('DASHBOARD')
                ],
                'action': 'loadDashboardView',
                'menu_id': 'dashboard'
            },
            'user-profile': {
                'title': 'User Profile',
                'breadcumb': [
                    _('HOME'),
                    _('PROFILE')
                ],
                'action': 'loadUserProfileView',
                'menu_id': 'user-profile'
            },
            'master-user': {
                'title': 'User Profile',
                'breadcumb': [
                    _('HOME'),
                    _('PROFILE')
                ],
                'action': 'loadMasterUserView',
                'menu_id': 'master-user',
                'data': {},
                'old_data': {}
            },
            'add-user': {
                'title': 'Add User',
                'breadcumb': [
                    _('HOME'),
                    _('PROFILE')
                ],
                'action': 'loadAddUserView',
                'menu_id': 'add-user',
            },
            'edit-user-profile': {
                'title': 'User Profile',
                'breadcumb': [
                    _('HOME'),
                    _('PROFILE')
                ],
                'action': 'showEditUserView',
                'menu_id': 'edit-user-profile'
            },
            'under-provisioning': {
                'title': 'Orders',
                'breadcumb': [
                    _('HOME'),
                    _('ORDERS'),
                    _('Under Provisioning')
                ],
                'action': 'loadOrderWIPView',
                'actionListView': 'updateOrderWIPListView',
                'menu_id': 'under-provisioning',
                'order': 'service_name ASC',
                'keyword': ''
            },
            'installed-services': {
                'title': 'Orders',
                'breadcumb': [
                    _('HOME'),
                    _('ORDERS'),
                    _('Installed Services')
                ],
                'action': 'loadOrderInstalledView',
                'actionListView': 'updateOrderInstalledListView',
                'actionDownload': 'downloadInstalledService',
                'menu_id': 'installed-services',
                'order': 'service_name ASC',
                'keyword': ''
            },
            'remote-hands': {
                'title': 'Orders',
                'breadcumb': [
                    _('HOME'),
                    _('ORDERS'),
                    _('Request Services'),
                    _('Remote Hands')
                ],
                'action': 'loadRemoteHandsView',
                'menu_id': 'remote-hands',
                'project_id': 0
            },
            'interconnection-services': {
                'title': 'Orders',
                'breadcumb': [
                    _('HOME'),
                    _('ORDERS'),
                    _('Request Services'),
                    _('Interconnection Services')
                ],
                'action': 'loadInterconnectionServicesView',
                'menu_id': 'interconnection-services'
            },
            # 'colocation-acessories': {
            #     'title': 'Orders',
            #     'breadcumb': [
            #         _('HOME'),
            #         _('ORDERS'),
            #         _('Request Services'),
            #         _('Colocation Accessories')
            #     ],
            #     'action': 'loadColocationAccessoriesView',
            #     'menu_id': 'colocation-accessories'
            # },
            'invoice': {
                'title': 'Invoice',
                'breadcumb': [
                    _('HOME'),
                    _('INVOICE')
                ],
                'action': 'loadInvoiceView',
                'actionListView': 'updateOrderInvoiceListView',
                'actionDownload': 'downloadInvoice',
                'menu_id': 'invoice',
                'order': 'invoice_number ASC',
                'keyword': ''
            },
            'new-fault-report-ticket': {
                'title': 'Ticketing',
                'breadcumb': [
                    _('HOME'),
                    _('Ticketing'),
                    _('New Fault Report Ticket')
                ],
                'action': 'loadFaultReportView',
                'menu_id': 'new-fault-report-ticket'
            },
            'new-site-access-ticket': {
                'title': 'Ticketing',
                'breadcumb': [
                    _('HOME'),
                    _('Ticketing'),
                    _('New Site Access Ticket')
                ],
                'action': 'loadSiteAccessView',
                'menu_id': 'new-site-access-ticket'
            },
            'new-shipment-ticket': {
                'title': 'Ticketing',
                'breadcumb': [
                    _('HOME'),
                    _('Ticketing'),
                    _('New Shipment Ticket')
                ],
                'action': 'loadShipmentView',
                'menu_id': 'new-shipment-ticket'
            },
            'ticket-list-table': {
                'title': 'Ticketing',
                'breadcumb': [
                    _('HOME'),
                    _('Ticketing'),
                    _('Ticket List')
                ],
                'action': 'loadTicketListTableView',
                'actionListView': 'updateOrderTicketListView',             
                'menu_id': 'ticket-list-table',
                'order': 'write_date DESC',
                'keyword': ''
            },
            'contact-us': {
                'title': 'Contact Us',
                'breadcumb': [
                    _('HOME'),
                    _('CONTACT US')
                ],
                'action': 'loadContactUs',
                'actionListView': 'updateContact',
                'menu_id': 'contact-us'
            },
            'feedbacks': {
                'title': 'Feedbacks',
                'breadcumb': [
                    _('HOME'),
                    _('CONTACT US')
                ],
                'action': 'openEmail',
                'menu_id': 'feedbacks'
            },
            'policies': {
                'title': 'Documents',
                'breadcumb': [
                    _('HOME'),
                    _('DOCUMENTS'),
                    _('POLICIES')
                ],
                'action': 'loadPolicies',
                'actionListView': 'updatePolicies',
                'menu_id': 'policies'
            },
            'faq': {
                'title': 'Documents',
                'breadcumb': [
                    _('HOME'),
                    _('DOCUMENTS'),
                    _('FAQ')
                ],
                'action': 'loadFAQ',
                'actionListView': 'updateFAQ',
                'menu_id': 'faq'
            },
            'policies': {
                'title': 'Documents',
                'breadcumb': [
                    _('HOME'),
                    _('DOCUMENTS'),
                    _('POLICIES')
                ],
                'action': 'loadPolicies',
                'actionListView': 'updatePolicies',
                'menu_id': 'policies'
            },
            'message-list': {
                'title': 'Message List',
                'breadcumb': [
                    _('HOME'),
                    _('DASHBOARD'),
                    _('Message List')
                ],
                'action': 'loadMessageListView',
                'actionListView': 'updateMessageListView',             
                'menu_id': 'message-list',
                'order': '',
                'keyword': ''
            },            
            'message-detail': {
                'title': 'Message Detail',
                'breadcumb': [
                    _('HOME'),
                    _('DASHBOARD'),
                    _('Message List'),
                    _('Message Detail')
                ],
                'action': 'loadMessageDetailView',         
                'menu_id': 'message-detail',
            },
            'notification-list': {
                'title': 'Notification List',
                'breadcumb': [
                    _('HOME'),
                    _('DASHBOARD'),
                    _('Notification List')
                ],
                'action': 'loadNotificationListView',
                'actionListView': 'updateNotificationListView',             
                'menu_id': 'notification-list',
                'order': '',
                'keyword': ''
            },            
            'notification-detail': {
                'title': 'Notification Detail',
                'breadcumb': [
                    _('HOME'),
                    _('DASHBOARD'),
                    _('Notification List'),
                    _('Notification Detail')
                ],
                'action': 'loadNotificationDetailView',         
                'menu_id': 'notification-detail',
            },
        }

        has_admin_right = portal_helper.has_access_right(request.env.user.partner_id, 'Primary Access Administrator')
        has_provisioning_right = portal_helper.has_access_right(request.env.user.partner_id, 'Provisioning')
        has_remote_hand_right = portal_helper.has_access_right(request.env.user.partner_id, 'Remote Hands')
        has_ordering_right = portal_helper.has_access_right(request.env.user.partner_id, 'Ordering')
        has_invoicing_right = portal_helper.has_access_right(request.env.user.partner_id, 'Invoicing')
        has_marketplace_right = portal_helper.has_access_right(request.env.user.partner_id, 'Marketplace')
        has_fault_report_right = portal_helper.has_access_right(request.env.user.partner_id, 'Fault Report')
        has_site_access_right = portal_helper.has_access_right(request.env.user.partner_id, 'Site Access Ticket')
        has_shipment_right = portal_helper.has_access_right(request.env.user.partner_id, 'Shipment Ticket')

        if not has_admin_right:
            route.pop('master-user',None)
            route.pop('add-user',None)

        if not has_provisioning_right:
            route.pop('under-provisioning',None)
            route.pop('installed-services',None)

        if not has_remote_hand_right:
            route.pop('remote-hands',None)

        if not has_ordering_right:
            route.pop('interconnection-services',None)
            route.pop('colocation-accessories',None)

        if not has_invoicing_right:
            route.pop('invoice',None)

        if not has_fault_report_right:
            route.pop('new-fault-report-ticket',None)

        if not has_site_access_right:
            route.pop('new-site-access-ticket',None)

        if not has_shipment_right:
            route.pop('new-shipment-ticket',None)

        return route

    @route(['/portal'], type='http', auth="user", website=True)
    def portal_index(self, **kw):

        host_url = request.httprequest.host_url
        portal_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_portal_url')
        erp_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url')

        # if portal_domain in host_url:
        if erp_domain:
            if erp_domain in host_url:
                return http.local_redirect('/web/login?error=access&err_domain=erp')

        default_menuitems = [
            {
                'type': 'parent_menu_item',
                'menu_id': 'dashboard',
                'icon': 'de-ic-dashboard',
                'label': _('DASHBOARD'),
                'name': 'DASHBOARD',
                'child': [
                    {
                        'type': 'menu_item',
                        'menu_id': 'message-list',
                        'icon': '',
                        'label': _('Message List'),
                        'name': 'Under Provisioning',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'notification-list',
                        'icon': '',
                        'label': _('Notification List'),
                        'name': 'Installed Services',
                        'child': []
                    },
                ]
            },
            {
                'type': 'parent_menu',
                'menu_id': '',
                'icon': 'de-ic-order',
                'label': _('ORDERS'),
                'name': 'ORDERS',
                'child': [
                    {
                        'type': 'menu_item',
                        'menu_id': 'under-provisioning',
                        'icon': '',
                        'label': _('Under Provisioning'),
                        'name': 'Under Provisioning',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'installed-services',
                        'icon': '',
                        'label': _('Installed Services'),
                        'name': 'Installed Services',
                        'child': []
                    },
                    {
                        'type': 'sub_parent_menu',
                        'menu_id': 'request-services',
                        'icon': '',
                        'label': _('Request Services'),
                        'name': 'Request Services',
                        'child': [
                            {
                                'type': 'menu_item',
                                'menu_id': 'remote-hands',
                                'icon': '',
                                'label': _('Remote Hands'),
                                'name': 'Remote Hands',
                                'child': []
                            },
                            {
                                'type': 'menu_item',
                                'menu_id': 'interconnection-services',
                                'icon': '',
                                'label': _('Interconnection Services'),
                                'name': 'Interconnection Services',
                                'child': []
                            },
                            # {
                            #     'type': 'menu_item',
                            #     'menu_id': 'colocation-acessories',
                            #     'icon': '',
                            #     'label': _('Colocation Accessories'),
                            #     'name': 'Colocation Accessories',
                            #     'child': []
                            # },
                        ]
                    },
                ]
            },
            {
                'type': 'menu_item',
                'menu_id': 'invoice',
                'icon': 'de-ic-invoice',
                'label': _('INVOICE'),
                'name': 'INVOICE',
                'child': []
            },
            {
                'type': 'menu_item',
                'menu_id': 'marketplace',
                'icon': 'fa fa-calendar',
                'label': _('MARKETPLACE'),
                'name': 'MARKETPLACE',
                'child': []
            },
            {
                'type': 'parent_menu',
                'menu_id': '',
                'icon': 'de-ic-ticketing',
                'label': _('TICKETING'),
                'name': 'TICKETING',
                'child': [
                    {
                        'type': 'menu_item',
                        'menu_id': 'new-fault-report-ticket',
                        'icon': '',
                        'label': _('New Fault Report Ticket'),
                        'name': 'New Fault Report Ticket',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'new-site-access-ticket',
                        'icon': '',
                        'label': _('New Site Access Ticket'),
                        'name': 'New Site Access Ticket',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'new-shipment-ticket',
                        'icon': '',
                        'label': _('New Shipment Ticket'),
                        'name': 'New Shipment Ticket',
                        'child': []
                    },                    
                    {
                        'type': 'menu_item',
                        'menu_id': 'ticket-list-table',
                        'icon': '',
                        'label': _('Ticket List'),
                        'name': 'Ticket List',
                        'child': []
                    },
                ]
            },
            {
                'type': 'parent_menu',
                'menu_id': '',
                'icon': 'de-ic-documents',
                'label': _('DOCUMENTS'),
                'name': 'DOCUMENTS',
                'child': [
                    {
                        'type': 'menu_item',
                        'menu_id': 'policies',
                        'icon': '',
                        'label': _('Policies'),
                        'name': 'Policies',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'faq',
                        'icon': '',
                        'label': _('FAQ'),
                        'name': 'FAQ',
                        'child': []
                    },
                ]
            },
            {
                'type': 'parent_menu',
                'menu_id': '',
                'icon': 'de-ic-contact',
                'label': _('CONTACT US'),
                'name': 'CONTACT US',
                'child': [
                    {
                        'type': 'menu_item',
                        'menu_id': 'contact-us',
                        'icon': '',
                        'label': _('Region Contacts'),
                        'name': 'Region Contacts',
                        'child': []
                    },
                    {
                        'type': 'menu_item',
                        'menu_id': 'feedbacks',
                        'icon': '',
                        'label': _('Feedbacks'),
                        'name': 'Feedbacks',
                        'child': []
                    },
                ]
            }            
        ];
        menuitems = []
        for m_item in default_menuitems:
            if m_item['name'] == 'DASHBOARD':
                menuitems.append(m_item)

            elif m_item['name'] == 'ORDERS':
                temp = m_item.copy()
                temp['child'] = []
                has_provisioning_right = portal_helper.has_access_right(request.env.user.partner_id, 'Provisioning')
                if has_provisioning_right:
                    temp['child'].append(m_item['child'][0])
                    temp['child'].append(m_item['child'][1])
                
                has_remote_hand_right = portal_helper.has_access_right(request.env.user.partner_id, 'Remote Hands')
                has_ordering_right = portal_helper.has_access_right(request.env.user.partner_id, 'Ordering')
                if has_remote_hand_right or has_ordering_right:
                    temp2 = m_item['child'][2].copy()
                    temp2['child'] = []                    

                    if has_remote_hand_right:
                        temp2['child'].append(m_item['child'][2]['child'][0])

                    if has_ordering_right:
                        temp2['child'].append(m_item['child'][2]['child'][1])
                        # temp2['child'].append(m_item['child'][2]['child'][2])

                    temp['child'].append(temp2)

                if len(temp['child']) > 0:
                    menuitems.append(temp)

            elif m_item['name'] == 'INVOICE':
                has_invoicing_right = portal_helper.has_access_right(request.env.user.partner_id, 'Invoicing')
                if has_invoicing_right:
                    menuitems.append(m_item)

            elif m_item['name'] == 'MARKETPLACE':
                has_marketplace_right = portal_helper.has_access_right(request.env.user.partner_id, 'Marketplace')
                if has_marketplace_right:
                    menuitems.append(m_item)

            elif m_item['name'] == 'TICKETING':
                temp = m_item.copy()
                temp['child'] = []
                
                has_fault_report_right = portal_helper.has_access_right(request.env.user.partner_id, 'Fault Report')
                if has_fault_report_right:
                    temp['child'].append(m_item['child'][0])

                has_site_access_right = portal_helper.has_access_right(request.env.user.partner_id, 'Site Access Ticket')
                if has_site_access_right:
                    temp['child'].append(m_item['child'][1])

                has_shipment_right = portal_helper.has_access_right(request.env.user.partner_id, 'Shipment Ticket')
                if has_shipment_right:
                    temp['child'].append(m_item['child'][2])

                if has_fault_report_right or has_site_access_right or has_shipment_right:
                    temp['child'].append(m_item['child'][3])

                if len(temp['child']) > 0:
                    menuitems.append(temp)

            elif m_item['name'] == 'DOCUMENTS':
                menuitems.append(m_item)

            elif m_item['name'] == 'CONTACT US':
                menuitems.append(m_item)

        current_cookies = dict(request.httprequest.cookies)
        active_companies = []
        if current_cookies.get('acids'):
            active_companies = current_cookies.get('acids').split(",")
        
        companies = []
        for company in request.env.user.partner_id.x_studio_associated_company:
            if company.nrs_company_type != 'person':
                companies.append({
                    'name': company.name,
                    'active': True if str(company.id) in active_companies or len(active_companies) == 0 else False,
                    'id': company.id
                })

        languages = []
        selected_language = ''
        for language in request.env['res.lang'].sudo().get_available():
            languages.append({
                'name': language[2],
                'code': language[1]
            })

            if current_cookies.get('frontend_lang','en_US') == language[0]:
                selected_language = language[2]

        data = {
            'menuitems': menuitems,
            'user_name': _("Welcome, %s", request.env.user.partner_id.name),
            'user_photo': '/portal/partner_image/%s?unique=%s' % (request.env.user.partner_id.id,datetime.strftime(datetime.now(),'%H%m%s')) if request.env.user.partner_id.image_1920 else '/nrs_de_portal/static/src/img/user.svg',
            'companies': companies,
            'languages': languages,
            'selected_language': selected_language,
            'company' : 'digital-edge',
        }
        #chuanjun website        
        # base_url = request.httprequest.host
        host_url = request.httprequest.host_url
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        # if base_url == "nervous-penguin-39.telebit.io":
        if chuanjun_domain and chuanjun_domain in host_url:
            data['company'] = "chuanjun"
        response = request.render("nrs_de_portal.de_portal_index", data)

        return response

    @route(['/contact'], type='http', auth="public", website=True)
    def portal_contaxt(self, **kw):
        data = {
            'company' : 'digital-edge',
        }
        #chuanjun website
        # base_url = request.httprequest.host
        # if base_url == "nervous-penguin-39.telebit.io":
        #     data['company'] = "chuanjun"
        host_url = request.httprequest.host_url
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        if chuanjun_domain and chuanjun_domain in host_url:
            data['company'] = "chuanjun"
        response = request.render("nrs_de_portal.de_portal_contact", data)
        return response

    @route(['/dashboard'], type='json', auth="user", website=False)
    def get_dashboard_data(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        notifications = []
        order_messages = []
        helpdesk_messages = []
        project_messages = []
        translated_term = {}
        
        has_provisioning_right = portal_helper.has_access_right(request.env.user.partner_id, 'Provisioning')
        has_remote_hand_right = portal_helper.has_access_right(request.env.user.partner_id, 'Remote Hands')
        has_ordering_right = portal_helper.has_access_right(request.env.user.partner_id, 'Ordering')
        has_invoicing_right = portal_helper.has_access_right(request.env.user.partner_id, 'Invoicing')
        has_marketplace_right = portal_helper.has_access_right(request.env.user.partner_id, 'Marketplace')
        has_fault_report_right = portal_helper.has_access_right(request.env.user.partner_id, 'Fault Report')
        has_site_access_right = portal_helper.has_access_right(request.env.user.partner_id, 'Site Access Ticket')
        has_shipment_right = portal_helper.has_access_right(request.env.user.partner_id, 'Shipment Ticket')        
        has_ticketing_right = has_remote_hand_right or has_fault_report_right or has_site_access_right or has_shipment_right

        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        notifs = request.env['nrs.notification'].sudo().search([('nrs_start_date','<=', fields.Date.today())])
        for notif in notifs:
            allowed = True
            if notif.nrs_end_date:
                if notif.nrs_end_date < fields.Date.today():
                    allowed = False

            if allowed:
                domain = safe_eval(notif.nrs_domain)
                partners = request.env['res.partner'].sudo().search(domain)

                if request.env.user.partner_id.id not in partners.ids:
                    allowed = False

            if allowed:
                ignored_partner = notif.nrs_ignore_partner_id.split(",") if notif.nrs_ignore_partner_id else []
                if str(request.env.user.partner_id.id) in ignored_partner:
                    allowed = False

            if allowed:
                notifications.append({
                    'id': notif.id,
                    'subject': notif.nrs_subject,
                    'body': notif.nrs_body
                })


        if has_ordering_right :
            orders = request.env['sale.order'].sudo().search([('state','=', 'sent'),('partner_id','in', allowed_companies)])
            for order in orders:
                for message in order.message_ids:
                    if message.message_type == 'comment':
                        attachment_ids = []
                        for attachment in message.attachment_ids:
                            attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        order_messages.append({
                            'id': message.id,
                            'author': message.author_id.name,
                            'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                            'body': message.body.replace("\n","<br/>"),
                            'record_name': message.record_name,
                            'menu_id': '',
                            'can_open': False,
                            'attachment_ids': attachment_ids
                        })

        if has_fault_report_right:
            helpdesks = request.env['helpdesk.ticket'].sudo().search([('stage_id.name','=', 'Pending Customer'),('x_studio_designated_company','in', allowed_companies)])
            for helpdesk in helpdesks:
                for message in helpdesk.message_ids:
                    if message.message_type == 'comment' or message.message_type == 'email':
                        
                        if message.subtype_id:
                            if message.subtype_id.name == "Note" :
                                continue

                        menu_id, can_open, menu_type = self._get_message_menu_id('helpdesk.ticket',helpdesk.id)       
                        attachment_ids = []

                        if not message.body or message.body == '':
                            temp_msg_body = message.subtype_id.name
                        else:
                            temp_msg_body = message.body.replace("\n","<br/>")

                        for attachment in message.attachment_ids:
                            attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        helpdesk_messages.append({
                            'id': message.id,
                            'author': message.author_id.name,
                            'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                            'body': temp_msg_body,
                            'record_name': message.record_name,
                            'menu_id': menu_id,
                            'can_open': can_open,
                            'attachment_ids': attachment_ids,
                            'team_id' : helpdesk.team_id.name
                        })

        if has_provisioning_right:
            projects = request.env['project.task'].sudo().search([('stage_id.name','=', 'Customer Acceptance'),('partner_id','in', allowed_companies)])
            for project in projects:
                for message in project.message_ids:
                    if message.message_type == 'comment':
                        menu_id, can_open, menu_type = self._get_message_menu_id('project.task',project.id)       
                        attachment_ids = []
                        for attachment in message.attachment_ids:
                            attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        project_messages.append({
                            'id': message.id,
                            'author': message.author_id.name,
                            'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                            'body': message.body.replace("\n","<br/>"),
                            'record_name': message.record_name,
                            'menu_id': menu_id,
                            'can_open': can_open,
                            'attachment_ids': attachment_ids
                        })

        action_count = len(order_messages) + len(helpdesk_messages) + len(project_messages)
        action_count = str(action_count).rjust(2,'0')      

        # global_messages = []
        # g_query = """
        #     SELECT DISTINCT
        #         f.res_model,
        #         f.res_id
        #     FROM mail_followers f
        #     WHERE f.partner_id in %s
        #     ORDER BY f.res_model
        # """
        # params = (allowed_companies,)
        # request.env.cr.execute(g_query, params)
        # result = request.env.cr.dictfetchall()

        # for res in result:
        #     search_domain = [('message_type','in', ['email', 'comment']), ('model','=',res['res_model']), ('res_id','=',res['res_id'])]
        #     messages = request.env['mail.message'].sudo().search(search_domain)
        #     for message in messages:
        #         ignored_partner = message.nrs_ignore_partner_id.split(",") if message.nrs_ignore_partner_id else []
        #         if str(request.env.user.partner_id.id) not in ignored_partner:
        #         # if True:
        #             menu_id, can_open, menu_type = self._get_message_menu_id(res['res_model'],res['res_id'])

        #             can_view = True
        #             if menu_type == "remote_hand":
        #                 if not has_remote_hand_right:
        #                     can_view = False
        #             elif menu_type == "fault_report":
        #                 if not has_fault_report_right:
        #                     can_view = False                   
        #             elif menu_type == "site_access":
        #                 if not has_site_access_right:
        #                     can_view = False                    
        #             elif menu_type == "shipment":
        #                 if not has_shipment_right:
        #                     can_view = False                     
        #             elif menu_type == "invoicing":
        #                 if not has_invoicing_right:
        #                     can_view = False                     
        #             elif menu_type == "provisioning":
        #                 if not has_provisioning_right:
        #                     can_view = False                      
        #             elif menu_type == "ordering":
        #                 if not has_ordering_right:
        #                     can_view = False     

        #             attachment_ids = []
        #             for attachment in message.attachment_ids:
        #                 attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))

        #             if not message.body or message.body == '':
        #                 temp_msg_body = message.subtype_id.name
        #             else:
        #                 temp_msg_body = message.body.replace("\n","<br/>")

        #             if can_view:
        #                 global_messages.append({
        #                     'id': message.id,
        #                     'author': message.author_id.name,
        #                     'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
        #                     'body': temp_msg_body,
        #                     'record_name': message.record_name,
        #                     'menu_id': menu_id,
        #                     'can_open': can_open,
        #                     'attachment_ids': attachment_ids
        #                 })
        
        global_messages = []
        g_query = """
            SELECT id
            FROM mail_message m
            WHERE 
                m.message_type IN ('email', 'comment') AND
                CONCAT_WS('_',m.model,m.res_id) IN (
                    SELECT
                        CONCAT_WS('_',f.res_model,f.res_id) AS code
                    FROM mail_followers f
                    WHERE f.partner_id = %s
                )
        """        
        # params = (allowed_companies,)
        params = (request.env.user.partner_id.id,)
        request.env.cr.execute(g_query, params)
        results = request.env.cr.dictfetchall()
        messages_id = [d['id'] for d in results]
        messages = request.env['mail.message'].sudo().browse(messages_id)
        for message in messages:            
            if message.subtype_id:
                if message.subtype_id.name == "Note" :
                    continue
            if message.message_type == "email":
                if request.env.user.partner_id.id not in message.partner_ids.ids:
                    continue
            ignored_partner = message.nrs_ignore_partner_id.split(",") if message.nrs_ignore_partner_id else []
            if str(request.env.user.partner_id.id) not in ignored_partner:
            # if True:
                menu_id, can_open, menu_type = self._get_message_menu_id(message['model'],message['res_id'])

                can_view = True
                if menu_type == "remote_hand":
                    if not has_remote_hand_right:
                        can_view = False
                elif menu_type == "fault_report":
                    if not has_fault_report_right:
                        can_view = False                   
                elif menu_type == "site_access":
                    if not has_site_access_right:
                        can_view = False                    
                elif menu_type == "shipment":
                    if not has_shipment_right:
                        can_view = False                     
                elif menu_type == "invoicing":
                    if not has_invoicing_right:
                        can_view = False                     
                elif menu_type == "provisioning":
                    if not has_provisioning_right:
                        can_view = False                      
                elif menu_type == "ordering":
                    if not has_ordering_right:
                        can_view = False     

                attachment_ids = []
                for attachment in message.attachment_ids:
                    attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))

                if not message.body or message.body == '':
                    temp_msg_body = message.subtype_id.name
                else:
                    temp_msg_body = message.body.replace("\n","<br/>")

                if can_view:
                    global_messages.append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids
                    })
        company = ""
        host_url = request.httprequest.host_url
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        if chuanjun_domain and chuanjun_domain in host_url:
            company = "chuanjun"

        translated_term['Actions'] = _('Actions')
        
        return {
            'notifications': notifications,
            'order_messages': order_messages,
            'helpdesk_messages': helpdesk_messages,
            'project_messages': project_messages,
            'global_messages': global_messages,
            'message_count': len(global_messages),
            'action_count': action_count,
            'has_provisioning_right': has_provisioning_right,
            'has_remote_hand_right': has_remote_hand_right,
            'has_ordering_right': has_ordering_right,
            'has_invoicing_right': has_invoicing_right,
            'has_marketplace_right': has_marketplace_right,
            'has_fault_report_right': has_fault_report_right,
            'has_site_access_right': has_site_access_right,
            'has_shipment_right': has_shipment_right,
            'has_ticketing_right': has_ticketing_right,
            'company': company,
            'translated_term': translated_term
        }

    @route(['/dashboard-messages'], type='json', auth="user", website=False)
    def get_dashboard_messages_data(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        notifications = []
        order_messages = []
        helpdesk_messages = []
        project_messages = []
        
        has_provisioning_right = portal_helper.has_access_right(request.env.user.partner_id, 'Provisioning')
        has_remote_hand_right = portal_helper.has_access_right(request.env.user.partner_id, 'Remote Hands')
        has_ordering_right = portal_helper.has_access_right(request.env.user.partner_id, 'Ordering')
        has_invoicing_right = portal_helper.has_access_right(request.env.user.partner_id, 'Invoicing')
        has_marketplace_right = portal_helper.has_access_right(request.env.user.partner_id, 'Marketplace')
        has_fault_report_right = portal_helper.has_access_right(request.env.user.partner_id, 'Fault Report')
        has_site_access_right = portal_helper.has_access_right(request.env.user.partner_id, 'Site Access Ticket')
        has_shipment_right = portal_helper.has_access_right(request.env.user.partner_id, 'Shipment Ticket')

        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        global_messages = []
        g_query = """
            SELECT DISTINCT
                f.res_model,
                f.res_id
            FROM mail_followers f
            WHERE f.partner_id in %s
            ORDER BY f.res_model
        """

        # params = (allowed_companies,)
        params = (request.env.user.partner_id.id,)
        request.env.cr.execute(g_query, params)
        result = request.env.cr.dictfetchall()

        for res in result:
            search_domain = [('message_type','in', ['email', 'comment']), ('model','=',res['res_model']), ('res_id','=',res['res_id'])]
            messages = request.env['mail.message'].sudo().search(search_domain, order='date desc')
            for message in messages:
                ignored_partner = message.nrs_ignore_partner_id.split(",") if message.nrs_ignore_partner_id else []
                if str(request.env.user.partner_id.id) not in ignored_partner:
                    menu_id, can_open, menu_type = self._get_message_menu_id(res['res_model'],res['res_id'])

                    can_view = True
                    if menu_type == "remote_hand":
                        if not has_remote_hand_right:
                            can_view = False
                    elif menu_type == "fault_report":
                        if not has_fault_report_right:
                            can_view = False                   
                    elif menu_type == "site_access":
                        if not has_site_access_right:
                            can_view = False                    
                    elif menu_type == "shipment":
                        if not has_shipment_right:
                            can_view = False                     
                    elif menu_type == "invoicing":
                        if not has_invoicing_right:
                            can_view = False                     
                    elif menu_type == "provisioning":
                        if not has_provisioning_right:
                            can_view = False                      
                    elif menu_type == "ordering":
                        if not has_ordering_right:
                            can_view = False     

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))

                    if not message.body or message.body == '':
                        temp_msg_body = message.subtype_id.name
                    else:
                        temp_msg_body = message.body.replace("\n","<br/>")

                    if can_view:
                        global_messages.append({
                            'id': message.id,
                            'author': message.author_id.name,
                            'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                            'body': temp_msg_body,
                            'record_name': message.record_name,
                            'menu_id': menu_id,
                            'can_open': can_open,
                            'attachment_ids': attachment_ids
                        })
            return {
                'data': global_messages,
            }

    def _get_message_menu_id(self, model='', id=0, return_ref_id = False):
        menu_id = ''
        menu_type = ''
        can_open = False
        ref_id = ''
        data = request.env[model].sudo().browse(id)
        if data:
            if model == 'helpdesk.ticket':
                if 'Remote Hands' in data.team_id.name:
                    menu_id = '#menu_id=remote-hands&action=read&ticket_id=%s' %(str(data.id))
                    menu_type = "remote_hand"
                    ref_id = str(data.id)
                elif 'Fault Report' in data.team_id.name:
                    menu_id = '#menu_id=new-fault-report-ticket&action=read&ticket_id=%s' %(str(data.id))
                    menu_type = "fault_report"
                    ref_id = str(data.id)
                elif 'Site Access' in data.team_id.name:
                    menu_id = '#menu_id=new-site-access-ticket&action=read&ticket_id=%s' %(str(data.id))                    
                    menu_type = "site_access"
                    ref_id = str(data.id)
                elif 'Shipment' in data.team_id.name:
                    menu_id = '#menu_id=new-shipment-ticket&action=read&ticket_id=%s' %(str(data.id))                    
                    menu_type = "shipment"
                    ref_id = str(data.id)

            if model == 'account.move':
                search_param = ''
                if data.ref:
                    search_param = 'Invoice Number->%s|Reference Number->%s' %(data.name, data.ref)
                else:
                    search_param = 'Invoice Number->%s' %(data.name)
                menu_id = '#menu_id=invoice&highlight=%s&search_param=%s' %(str(data.id), search_param)                    
                menu_type = "invoicing"                
                ref_id = str(data.id)

            if model == 'project.task':
                if 'Installed Base' in data.project_id.name:
                    if data.stage_id.name in ('Customer Acceptance','Pending Provisioning'):
                        search_param = 'Service ID->%s|Product Name->%s' %(data.x_studio_service_id, data.x_studio_product.name)
                        menu_id = '#menu_id=under-provisioning&highlight=%s&search_param=%s' %(str(data.id), search_param)
                    elif data.stage_id.name in ('In Service'):                        
                        search_param = 'Service ID->%s|Product->%s' %(data.x_studio_service_id, data.x_studio_product.name)
                        menu_id = '#menu_id=installed-services&highlight=%s&search_param=%s' %(str(data.id), search_param)                    
                    menu_type = "provisioning"                    
                    ref_id = str(data.id)

            if model == 'sale.order':                 
                menu_type = "ordering"
                ref_id = str(data.id)

        if menu_id != '':
            can_open = True

        if return_ref_id:
            return (menu_id,can_open,menu_type,ref_id)
        else:
            return (menu_id,can_open,menu_type)

    @route(['/dashboard/message-list'], type='json', auth="user", website=False)
    def get_message_list(self, **kwargs):
        message_data = {
            'remote_hand' : [],
            'fault_report' : [],
            'site_access' : [],
            'shipment' : [],
            'invoicing' : [],
            'provisioning' : [],
            'ordering' : []
        }

        has_provisioning_right = portal_helper.has_access_right(request.env.user.partner_id, 'Provisioning')
        has_remote_hand_right = portal_helper.has_access_right(request.env.user.partner_id, 'Remote Hands')
        has_ordering_right = portal_helper.has_access_right(request.env.user.partner_id, 'Ordering')
        has_invoicing_right = portal_helper.has_access_right(request.env.user.partner_id, 'Invoicing')
        has_marketplace_right = portal_helper.has_access_right(request.env.user.partner_id, 'Marketplace')
        has_fault_report_right = portal_helper.has_access_right(request.env.user.partner_id, 'Fault Report')
        has_site_access_right = portal_helper.has_access_right(request.env.user.partner_id, 'Site Access Ticket')
        has_shipment_right = portal_helper.has_access_right(request.env.user.partner_id, 'Shipment Ticket')

        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        g_query = """
            SELECT id
            FROM mail_message m
            WHERE 
                m.message_type IN ('email', 'comment') AND
                CONCAT_WS('_',m.model,m.res_id) IN (
                    SELECT
                        CONCAT_WS('_',f.res_model,f.res_id) AS code
                    FROM mail_followers f
                    WHERE f.partner_id = %s
                )
        """        
        # params = (allowed_companies,)
        params = (request.env.user.partner_id.id,)
        request.env.cr.execute(g_query, params)
        results = request.env.cr.dictfetchall()
        messages_id = [d['id'] for d in results]
        messages = request.env['mail.message'].sudo().browse(messages_id)
        for message in messages:
                       
            if message.subtype_id:
                if message.subtype_id.name == "Note" :
                    continue
            if message.message_type == "email":
                if request.env.user.partner_id.id not in message.partner_ids.ids:
                    continue
            
            menu_id, can_open, menu_type, ref_id = self._get_message_menu_id(message['model'],message['res_id'], True)

            if not message.body or message.body == '':
                temp_msg_body = message.subtype_id.name
            else:
                temp_msg_body = message.body.replace("\n","<br/>")

            if menu_type == "remote_hand":
                if has_remote_hand_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))

                    message_data['remote_hand'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        # 'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })
            elif menu_type == "fault_report":
                if has_fault_report_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['fault_report'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })                  
            elif menu_type == "site_access":
                if has_site_access_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['site_access'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })                    
            elif menu_type == "shipment":
                if has_shipment_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['shipment'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })                    
            elif menu_type == "invoicing":
                if has_invoicing_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['invoicing'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })                     
            elif menu_type == "provisioning":
                if has_provisioning_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['provisioning'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })                      
            elif menu_type == "ordering":
                if has_ordering_right:

                    attachment_ids = []
                    for attachment in message.attachment_ids:
                        attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                        
                    message_data['ordering'].append({
                        'id': message.id,
                        'author': message.author_id.name,
                        'date': message.date.astimezone(pytz.timezone('UTC')).isoformat(),
                        'body': temp_msg_body,
                        'record_name': message.record_name,
                        'menu_id': menu_id,
                        'can_open': can_open,
                        'attachment_ids': attachment_ids,
                        'ref_id': ref_id
                    })
        
        return message_data

    @route(['/dashboard/message-detail'], type='json', auth="user", website=False)
    def get_message_detail(self, **kwargs):              
        ref_model = kwargs.get('ref_model','')
        ref_id = portal_helper.get_default_int_value(kwargs.get('ref_id',''),'',0)

        logs = []
        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)
        
        model = request.env[ref_model].sudo().browse(ref_id)

        for message in model.message_ids.sorted(key=lambda r : r.id, reverse=True):
            if message.message_type in ['comment', 'email']:
                if message.subtype_id:
                    if message.subtype_id.name == "Note":
                        continue
                if message.message_type == "email":
                    if request.env.user.partner_id.id not in message.partner_ids.ids:
                        continue
                temp_msg_body = ""
                if not message.body or message.body == '':
                    temp_msg_body = message.subtype_id.name
                else:
                    temp_msg_body = message.body.replace("\n","<br/>")

                attachment_ids = []
                for attachment in message.attachment_ids:
                    attachment_ids.append('/web/content?download=true&id=%s&access_token=%s' % (attachment.id, attachment.sudo().generate_access_token()[0]))
                logs.append({
                    'author': message.author_id.name,
                    'date': datetime.strftime(message.date.astimezone(tz), '%H:%M, %d/%m/%Y'),
                    'body': temp_msg_body,
                    'attachment_ids': attachment_ids,
                    'record_name': message.record_name
                })

        return {
            'message' : logs,
            'ref_id': ref_id,
            'ref_model': ref_model
        }
    
    @route(['/message/reply'], type='json', auth="user", website=False)
    def reply_message(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ref_id = portal_helper.get_default_int_value(kwargs.get('ref_id',''),'',0)
        ref_model = kwargs.get('ref_model','')
        model = request.env[ref_model].sudo().browse(ref_id)
        message = kwargs.get('message','')

        if model:
            if len(message.strip()) > 0:
                attachments = kwargs.get('attachment',[])
                attachment_ids = []
                for attachment in attachments:
                    new_attachment = request.env['ir.attachment'].sudo().create({
                        'name': attachment['filename'],
                        'datas': attachment['data'],
                        'store_fname': attachment['filename'],
                        'res_model': 'mail.compose.message',
                    })
                    if new_attachment:
                        attachment_ids.append(new_attachment.id)
                
                model.sudo().message_post(author_id=request.env.user.partner_id.id,message_type='comment',body=message,subtype_xmlid='mail.mt_comment',attachment_ids=attachment_ids)
                # result['value']['logs'] = self._get_ticket_log( )
                # result['value']['id'] =  model.id
            else:
                result['status'] = 'restricted'
                result['message'] = _('Please write the message')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Model not found. Please try again.')

        return result

    @route(['/dashboard/notification-list'], type='json', auth="user", website=False)
    def get_notification_list(self, **kwargs):
        data = []
        notification = request.env['nrs.notification'].sudo().search([])

        for notif in notification:
            data.append({
                'id': notif.id,
                'subject': notif.nrs_subject,
                'notification_start_date': datetime.strftime(notif.nrs_start_date, '%Y-%m-%d'),
                'notification_end_date': datetime.strftime(notif.nrs_end_date, '%Y-%m-%d')
            })

        return {'data': data}

    @route(['/dashboard/notification-detail'], type='json', auth="user", website=False)
    def get_notification_detail(self, **kwargs):
        data = {
            'id': False,
            'subject': False,
            'notification_start_date': False,
            'notification_end_date': False,
            'body': False
        } 

        notification_id = portal_helper.get_default_int_value(kwargs.get('notif_id',''),'',0)      
        notification = request.env['nrs.notification'].sudo().browse(notification_id)

        if len(notification) > 0:
            for notif in notification:
                data = {
                    'id': notif.id,
                    'subject': notif.nrs_subject,
                    'notification_start_date': datetime.strftime(notif.nrs_start_date, '%Y-%m-%d'),
                    'notification_end_date': datetime.strftime(notif.nrs_end_date, '%Y-%m-%d'),
                    'body': notif.nrs_body
                }
        else:
            data = False

        return {'data': data}

    @route(['/hide/notification'], type='json', auth="user", website=False)
    def hide_notification(self, **kwargs):
        notif = portal_helper.get_default_int_value(kwargs.get('notif_id',''),'',0)
        notif_id = request.env['nrs.notification'].sudo().browse(notif)
        if notif_id:
            domain = safe_eval(notif_id.nrs_domain)
            partners = request.env['res.partner'].sudo().search(domain)
            if request.env.user.partner_id.id in partners.ids:
                ignored_partner = notif_id.nrs_ignore_partner_id.split(",") if notif_id.nrs_ignore_partner_id else []
                ignored_partner.append(str(request.env.user.partner_id.id))
                ignored_partner = ','.join(ignored_partner)

                notif_id.sudo().write({'nrs_ignore_partner_id': ignored_partner})

        return True

    @route(['/hide/message'], type='json', auth="user", website=False)
    def hide_message(self, **kwargs):
        message = portal_helper.get_default_int_value(kwargs.get('message_id',''),'',0)
        message_id = request.env['mail.message'].sudo().browse(message)
        if message_id:
            ignored_partner = message_id.nrs_ignore_partner_id.split(",") if message_id.nrs_ignore_partner_id else []
            ignored_partner.append(str(request.env.user.partner_id.id))
            ignored_partner = ','.join(ignored_partner)

            message_id.sudo().write({'nrs_ignore_partner_id': ignored_partner})

        return True
    
    @route(['/get-external-link'], type='json', auth="user", website=False)
    def get_external_link(self, **kwargs):
        link_type = kwargs.get('link_type','')
        link = request.env['nrs.external.link'].sudo().search([('nrs_type', '=', link_type)], limit=1)

        data = {
            'url' : '' 
        }
        if link:
            data['url'] = link.nrs_url
                    
        return data

    @route(['/get-url-settings'], type='json', auth="user", website=False)
    def get_url_settings(self, **kwargs):

        host_url = request.httprequest.host_url
        portal_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_portal_url')
        erp_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url')
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')

        return {
            'portal_domain' : portal_domain,
            'chuanjun_domain' : chuanjun_domain,
            'erp_domain' : erp_domain
        }