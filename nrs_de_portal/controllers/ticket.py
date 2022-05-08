# -*- coding: utf-8 -*-

import base64
import functools
import json
import logging
import math
import re
from base64 import decodestring
import magic
import os

from werkzeug import urls

from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route
from odoo.osv import expression
from odoo.tools import consteq
from datetime import datetime, timedelta
import pytz
from . import portal_helper

_logger = logging.getLogger(__name__)


class TicketPortal(Controller):

    @route(['/ticket/pricelist'], type='json', auth="user", website=False)
    def get_ticket_pricelist(self, **kwargs):
        price = 0
        currency = 'USD'

        ns_designated_company = False
        x_studio_operation_site = False
        # ns_service_id = False
        
        is_valid = True
        designated_company = portal_helper.get_default_int_value(kwargs.get('ns_designated_company',''),'',0)
        ns_designated_company = request.env['res.partner'].sudo().search([('id','=',designated_company)],limit=1)
        if not ns_designated_company:
            is_valid = False
        
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
            else:
                p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(ns_designated_company.ids, company_id=x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
                pricelist_id = p_list.get(ns_designated_company.id)
                currency = pricelist_id.currency_id.name

        # if is_valid:
        #     service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
        #     ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

        #     if not ns_service_id:
        #         is_valid = False
        
        if is_valid:
            p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(ns_designated_company.ids, company_id=x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
            pricelist_id = p_list.get(ns_designated_company.id)
            currency = pricelist_id.currency_id.name
            # if ns_service_id.timesheet_product_id:
            product_id = request.env['product.template'].sudo().search([('default_code','=','RMH001.NR')],limit=1)
            if product_id:
                operation_site_exist_in_product = False
                for os in product_id.x_studio_available_operation_site:
                    if os.name == x_studio_operation_site.name:
                        operation_site_exist_in_product = True
                if operation_site_exist_in_product:
                    price = pricelist_id.sudo().get_product_price(product_id, 1, ns_designated_company)

        if currency == "USD":
            currency_label = 'label_price_usd_per_hour'
            currency_label_default = 'USD / HOUR'
        elif currency == "IDR":
            currency_label = 'label_price_idr_per_hour'
            currency_label_default = 'IDR / HOUR'
        elif currency == "JPY":
            currency_label = 'label_price_jpy_per_hour'
            currency_label_default = 'JPY / HOUR'
        elif currency == "KRW":
            currency_label = 'label_price_krw_per_hour'
            currency_label_default = 'KRW / HOUR'
        elif currency == "CNY":
            currency_label = 'label_price_cny_per_hour'
            currency_label_default = 'CNY / HOUR'
        else:
            currency_label = 'none'
            currency_label_default = '%s / HOUR' % currency

        return {
            'price' : '{:20,.0f}'.format(price),
            'default_currency' : currency_label_default,
            'currency' : currency_label
        }

    @route(['/interconnection/pricelist'], type='json', auth="user", website=False)
    def get_interconnection_pricelist(self, **kwargs):
        mrc_price = 0
        nrc_price = 0
        mrc_product = ''
        nrc_product = ''
        currency = 'USD'

        partner_id = False
        x_studio_operation_site = False
        choose_service = kwargs.get('choose_service','')
        intra_customer = True if kwargs.get('intra_customer','') == 'on' else False
        media_type = kwargs.get('media_type','')
        quantity = kwargs.get('quantity', 1)

        if quantity == '':
            quantity = 0
        else:
            quantity = int(quantity)
        
        is_valid = True
        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        if not partner_id:
            is_valid = False
        
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
        
        if is_valid:
            mrc_product = choose_service
            if intra_customer:
                service_selection = request.env['nrs.req.service.selection'].sudo().search([('nrs_selection_type','=','intra_customer')],limit=1)
                if service_selection:
                    mrc_product += ' ' + service_selection.nrs_selection_value
                else:
                    mrc_product += ' Intra Customer'

            mrc_product += ' ' + media_type
            nrc_product = mrc_product

            


            nrc_postfix = request.env['nrs.req.service.selection'].sudo().search([('nrs_selection_type','=','nrc_postfix')],limit=1)
            if nrc_postfix:
                nrc_product += ' ' + nrc_postfix.nrs_selection_value
            else:
                nrc_product += ' Installation'
        
        
        if is_valid:
            p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(partner_id.ids, company_id=x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
            pricelist_id = p_list.get(partner_id.id)
            currency = pricelist_id.currency_id.name

            mrc_product_id = request.env['product.product'].sudo().search([('name','=',mrc_product)],limit=1)
            if mrc_product_id:
                mrc_price = pricelist_id.sudo().get_product_price(mrc_product_id, 1, partner_id)

            nrc_product_id = request.env['product.product'].sudo().search([('name','=',nrc_product)],limit=1)
            if nrc_product_id:
                nrc_price = pricelist_id.sudo().get_product_price(nrc_product_id, 1, partner_id)

        if intra_customer:
            temp_price = 'NRC %s %s' %('{:20,.0f}'.format(nrc_price * quantity), currency)
        else:   
            temp_price = 'MRC %s %s / NRC %s %s' %('{:20,.0f}'.format(mrc_price * quantity), currency, '{:20,.0f}'.format(nrc_price * quantity), currency)
        return {
            'mrc_product': mrc_product,
            'nrc_product': nrc_product,
            'price': temp_price
        }

    @route(['/colocation-accessories/pricelist'], type='json', auth="user", website=False)
    def get_colocation_accessories_pricelist(self, **kwargs):
        price = 0
        uom = 'Units'
        currency = 'USD'

        partner_id = False
        x_studio_operation_site = False
        product_id = False
        qty = 1
        
        is_valid = True
        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        if not partner_id:
            is_valid = False
        
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
            else:
                p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(partner_id.ids, company_id=x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
                pricelist_id = p_list.get(partner_id.id)
                currency = pricelist_id.currency_id.name

        if is_valid:
            product_template = portal_helper.get_default_int_value(kwargs.get('product_id',''),'',0)
            product_template_id = request.env['product.template'].sudo().search([('id','=',product_template)],limit=1)

            if not product_template_id:
                is_valid = False
        
               
        
        if is_valid:
            temp_qty = portal_helper.get_default_int_value(kwargs.get('qty',''),'',0)
            if temp_qty > 0:
                qty = temp_qty
            p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(partner_id.ids, company_id=x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
            pricelist_id = p_list.get(partner_id.id)
            currency = pricelist_id.currency_id.name

            product_id = product_template_id.product_variant_id
            price = pricelist_id.sudo().get_product_price(product_id, qty, partner_id)
            uom = product_id.uom_id.name            
            

        return {
            'price': '%s %s / %s' %('{:20,.0f}'.format(price), currency, uom)
        }

    def _get_operation_site(self, partner):
        data = []
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        query = """
            SELECT DISTINCT
                o_site.id,
                o_site.name,
                o_site.ns_timezone
            FROM operating_sites o_site
            JOIN project_task project ON project.x_studio_operation_site = o_site.id
            WHERE 
                project.partner_id IN %s AND
                o_site.id IN (
                    SELECT 
                        o_sites2.id
                    FROM project_task p_task
                    LEFT JOIN project_project p_project ON p_project.id = p_task.project_id
                    LEFT JOIN sale_order_line s_line ON s_line.id = p_task.sale_line_id
                    LEFT JOIN sale_order s_order ON s_order.id = s_line.order_id
                    LEFT JOIN product_product p_product ON p_product.id = s_line.product_id
                    LEFT JOIN product_template p_template ON p_template.id = p_product.product_tmpl_id
                    LEFT JOIN project_task_type p_task_type ON p_task_type.id = p_task.stage_id
                    LEFT JOIN operating_sites o_sites2 on o_sites2.id = p_task.x_studio_operation_site
                    WHERE 
                        p_task.partner_id in %s AND
                        p_project.name ilike %s AND
                        p_task_type.name in ('In Service')
                )

                
        """
        if type(partner) is tuple : 
            params = (partner,allowed_companies, '%Installed Base%')
        else:            
            params = (tuple([partner]),allowed_companies, '%Installed Base%')  
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()
        for res in result:
            data.append({'id': res['id'],'name': res['name'], 'selected': False, 'timezone': res['ns_timezone']})

        if len(data) == 1:
            data[0]['selected'] = True

        return data

    @route(['/get/operation-site'], type='json', auth="user", website=False)
    def get_operation_site(self, **kwargs):
        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)

        return {'data': self._get_operation_site(partner)}

    def _get_service_id(self, allowed_companies, partner, operation_site, product_categ, menu, additionalData = False):
        data = []       

        search_domain = [('project_id.name','ilike','Installed Base')]
        search_domain = expression.AND([search_domain,[('stage_id.name','in',['In Service'])]])
        search_domain = expression.AND([search_domain,[('x_studio_operation_site','=',operation_site)]])
        search_domain = expression.AND([search_domain,[('partner_id.id','in',allowed_companies)]])
        if additionalData:
            if not additionalData.get('is_fault_report', False):
                search_domain = expression.AND([search_domain,[('x_studio_product.categ_id.name','in',['Space'])]])

        if len(product_categ) > 0:
            search_domain = expression.AND([search_domain,[('x_studio_product_category.name','=',product_categ)]])

        if partner:
            search_domain = expression.AND([search_domain,[('partner_id','=',partner)]])
                 
        projects_count = request.env['project.task'].sudo().search_count(search_domain)            
        projects = request.env['project.task'].sudo().search(search_domain, limit = 7)
        
        # Initial name with space id

        for p in projects:
            temp_name = p.name
            if p.x_studio_product.ns_capacity_assignation == 'space_id':
                if p.x_studio_space_id.ns_name:
                    temp_name += " / " + str(p.x_studio_space_id.ns_name)
            elif p.x_studio_product.ns_capacity_assignation == 'breaker_id' or p.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                if p.x_studio_related_space_id.ns_name:
                    temp_name += " / " + str(p.x_studio_related_space_id.ns_name)

            data.append({'id': p.id,'name': temp_name, 'partner_id': p.partner_id.id, 'selected': False})
        
        if projects_count > 7:
            data.append({'id': 'other','name': 'show more...', 'partner_id': 'other', 'selected': False})

        if len(data) == 1:
            data[0]['selected'] = True

        if additionalData:
            if 'fromPopup' in additionalData:
                data.insert(0, {'id': additionalData['service_id'],'name': additionalData['service_name'], 'partner_id': additionalData['partner'], 'selected': True})
            if 'fromEdit' in additionalData:
                insertAdditionalData = True
                for d in data:  
                    if d['id'] == int(additionalData['service_id']):
                       insertAdditionalData = False
                if insertAdditionalData:
                    temp_projects = request.env['project.task'].sudo().search([('id', '=', additionalData['service_id'])], limit=1)
                    data.insert(0, {'id': temp_projects.id,'name': temp_projects.name, 'partner_id': temp_projects.partner_id.id, 'selected': True})
        return data

    @route(['/get/service-id'], type='json', auth="user", website=False)
    def get_service_id(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))

        menu = kwargs.get('menu',False)

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        if partner == '':
            partner = False

        service_id = kwargs.get('service_id',False)
        if service_id:
            service = request.env['project.task'].sudo().search([('id','=',service_id)])
            if service:
                partner = service.partner_id.id

        operation_site = portal_helper.get_default_int_value(kwargs.get('operation_site',''),'',0)
        product_categ = kwargs.get('product_categ','')
        additionalData = kwargs.get('additionalData',False)
        
        return {'data': self._get_service_id(allowed_companies, partner, operation_site, product_categ, menu, additionalData)}

    def _get_service_id_popup(self, allowed_companies, partner, operation_site, product_categ, menu, limit, offset, additionalData):

        # data = []       

        # if partner:
        #     projects_count = request.env['project.task'].sudo().search_count([
        #         ('partner_id','=',partner),
        #         ('project_id.name','ilike','Installed Base'),
        #         ('stage_id.name','in',['In Service']),
        #         ('x_studio_operation_site','=',operation_site)
        #     ])
        #     projects = request.env['project.task'].sudo().search([
        #         ('partner_id','=',partner),
        #         ('project_id.name','ilike','Installed Base'),
        #         ('stage_id.name','in',['In Service']),
        #         ('x_studio_operation_site','=',operation_site)
        #     ])
        # else:            
        #     projects_count = request.env['project.task'].sudo().search_count([
        #         ('project_id.name','ilike','Installed Base'),
        #         ('stage_id.name','in',['In Service']),
        #         ('x_studio_operation_site','=',operation_site)
        #     ])            
        #     projects = request.env['project.task'].sudo().search([
        #         ('project_id.name','ilike','Installed Base'),
        #         ('stage_id.name','in',['In Service']),
        #         ('x_studio_operation_site','=',operation_site)
        #     ])

        # for p in projects:
        #     if p.partner_id.id in allowed_companies:
        #         if menu == 'new-fault-report-ticket':
        #             if len(product_categ) > 0:
        #                 if p.x_studio_product_category.name == product_categ:
        #                     data.append({'id': p.id,'name': p.name, 'partner_id': p.partner_id.id, 'selected': False})
        #             else:
        #                 data.append({'id': p.id,'name': p.name, 'partner_id': p.partner_id.id, 'selected': False})
        #         else:
        #             if re.search("(?i)cabinet", p.name):
        #                 if len(product_categ) > 0:
        #                     if p.x_studio_product_category.name == product_categ:
        #                         data.append({'id': p.id,'name': p.name, 'partner_id': p.partner_id.id, 'selected': False})
        #                 else:
        #                     data.append({'id': p.id,'name': p.name, 'partner_id': p.partner_id.id, 'selected': False})

        data = [] 
        
        total = 0  

        search_domain = [('project_id.name','ilike','Installed Base')]
        search_domain = expression.AND([search_domain,[('stage_id.name','in',['In Service'])]])
        search_domain = expression.AND([search_domain,[('x_studio_operation_site','=',operation_site)]])
        search_domain = expression.AND([search_domain,[('partner_id.id','in',allowed_companies)]])
        if additionalData:
            if not additionalData.get('is_fault_report', False):
                search_domain = expression.AND([search_domain,[('x_studio_product.categ_id.name','in',['Space'])]])

        if len(product_categ) > 0:
            search_domain = expression.AND([search_domain,[('x_studio_product_category.name','=',product_categ)]])

        if partner:
            search_domain = expression.AND([search_domain,[('partner_id','=',partner)]])
                 
        projects_count = request.env['project.task'].sudo().search_count(search_domain)            
        projects = request.env['project.task'].sudo().search(search_domain, limit = limit, offset = offset)

        total = projects_count
        
        for p in projects:
            temp_name = p.name
            if p.x_studio_product.ns_capacity_assignation == 'space_id':
                if p.x_studio_space_id.ns_name:
                    temp_name += " / " + str(p.x_studio_space_id.ns_name)
            elif p.x_studio_product.ns_capacity_assignation == 'breaker_id' or p.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                if p.x_studio_related_space_id.ns_name:
                    temp_name += " / " + str(p.x_studio_related_space_id.ns_name)
            data.append({'id': p.id,'name': temp_name, 'partner_id': p.partner_id.id, 'selected': False})

        return {'data': data, 'limit' : limit, 'offset' : offset, 'total' : total}

    @route(['/get/service-id-popup'], type='json', auth="user", website=False)
    def get_service_id_popup(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))

        menu = kwargs.get('menu',False)        
        offset = kwargs['offset']
        limit = kwargs['limit']

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        if partner == '':
            partner = False

        service_id = kwargs.get('service_id',False)
        if service_id:
            service = request.env['project.task'].sudo().search([('id','=',service_id)])
            if service:
                partner = service.partner_id.id

        operation_site = portal_helper.get_default_int_value(kwargs.get('operation_site',''),'',0)
        product_categ = kwargs.get('product_categ','')
        additionalData =kwargs.get('additionalData', '')

        data = self._get_service_id_popup(allowed_companies, partner, operation_site, product_categ, menu, limit, offset, additionalData)['data']
        limit = self._get_service_id_popup(allowed_companies, partner, operation_site, product_categ, menu, limit, offset, additionalData)['limit']
        offset = self._get_service_id_popup(allowed_companies, partner, operation_site, product_categ, menu, limit, offset, additionalData)['offset']
        total = self._get_service_id_popup(allowed_companies, partner, operation_site, product_categ, menu, limit, offset, additionalData)['total']
        
        return {'data': data, 'limit' : limit, 'offset' : offset, 'total' : total}
    
    def _get_company_id(self, service_id):
        data = []  
        service = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)
        if service:
            data.append({'id': service.partner_id.id,'name': service.partner_id.name})

        if len(data) == 1:
            data[0]['selected'] = True

        return data
    
    @route(['/get/company-id'], type='json', auth="user", website=False)
    def get_company_id(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        service = portal_helper.get_default_int_value(kwargs.get('service_id',''),'',0)
        
        return {'data': self._get_company_id(service)}

    @route(['/get/ticket-type'], type='json', auth="user", website=False)
    def get_ticket_type(self, **kwargs):
        data = []
        operation_site = portal_helper.get_default_int_value(kwargs.get('operation_site',''),'',0)
        operation_site_id = request.env['operating.sites'].sudo().search([('id','=',operation_site)],limit=1)
        team = kwargs.get('team','')

        team_id = request.env['helpdesk.team'].sudo().search([
            ('company_id','=',operation_site_id.x_studio_country.x_studio_related_digital_edge_companies.id),
            ('name','ilike',team)
        ], limit=1)

        if team_id:
            ticket_types = request.env['helpdesk.ticket.type'].sudo().search([])
            for t_type in ticket_types:
                if team_id.id in t_type.x_studio_visibility.ids:
                    data.append({'id': t_type.id,'name': t_type.name})

        return {'data': data}

    def _get_area(self, operation_site_id):
        data = []
        rooms = request.env['ns.ns_rooms'].sudo().search([('ns_floor.ns_operation_site','=',operation_site_id.id)])
        
        for room in rooms:
            data.append({'id': room.id,'name': room.ns_name})

        return data

    @route(['/get/area'], type='json', auth="user", website=False)
    def get_area(self, **kwargs):
        data = []
        operation_site = portal_helper.get_default_int_value(kwargs.get('operation_site',''),'',0)
        operation_site_id = request.env['operating.sites'].sudo().search([('id','=',operation_site)],limit=1)

        return {'data': self._get_area(operation_site_id)}

    @route(['/ticket-list'], type='json', auth="user", website=False)
    def get_ticket_list(self, **kwargs):
        result = []

        menu = kwargs['menu_id']
        name = ""

        if menu == "remote-hands":
            name = "Remote Hands"
        elif menu == "new-fault-report-ticket":
            name = "Fault Report"
        elif menu == "new-site-access-ticket":
            name = "Site Access"
        elif menu == "new-shipment-ticket":
            name = "Shipment"

        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))

        search_domain = ['&', ('partner_id','=',request.env.user.partner_id.id), ('ns_designated_company','in', allowed_companies)]
        search_domain = expression.AND([search_domain,[('name', '=', name)]])
        search_domain = expression.AND([search_domain,[('stage_id.is_close', '!=', True)]])

        tickets = request.env['helpdesk.ticket'].sudo().search(search_domain)
        
        for ticket in tickets:

            display_name = ticket.display_name
            if ticket.ns_ticket_subject and ticket.ns_ticket_subject != '':
                display_name = display_name + " : " + ticket.ns_ticket_subject

            result.append({
                'id': ticket.id,
                'name': display_name,
                'stage': ticket.stage_id.name,
                'team': ticket.team_id.name,
                'create_date': datetime.strftime(ticket.create_date, '%Y-%m-%d') if ticket.create_date else '',
                'last_updated_date': datetime.strftime(ticket.write_date, '%Y-%m-%d') if ticket.write_date else ''
            })

        return result
    
    @route(['/ticket-list-table'], type='json', auth="user", website=False)
    def get_ticket_list_table(self, **kwargs):

        order = kwargs['order']
        offset = kwargs['offset']
        limit = kwargs['limit']
        total = 0
        search_term = kwargs.get('search_term',False)
        result = []
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))

        search_domain = ['&', ('partner_id','=',request.env.user.partner_id.id), ('ns_designated_company','in', allowed_companies)]

        if "name,id" in order:
            temp_order = order.split(' ')[1]
            temp_column = order.split(' ')[0].split(',')
            order = temp_column[0] + " " + temp_order + ", " + temp_column[1] + " " + temp_order

        # _logger.info("- order:")
        # _logger.info(order)
        
        if search_term != False:
            for search_data in search_term.split('|'):
                column = search_data.split('->')[0]
                value = search_data.split('->')[1]

                arrayValue = value.split(' or ')

                if column in ["name", "create_uid.name", "stage_id.name", "ticket_type_id.name", "x_studio_operation_site.name"]:
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
                        
                elif column in ["create_date", "write_date"]:
                    if len(arrayValue) > 1:
                        temp_domain = False
                        for val in arrayValue:
                            if temp_domain:
                                if re.search("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}$", val):
                                    temp_domain = expression.OR([temp_domain,expression.AND([[(column, '>=', val + ' 00:00:00')],[(column, '<=', val + ' 23:59:59')]])])
                                else:
                                    temp_domain = expression.OR([temp_domain,[(column, 'ilike', val)]])
                            else:
                                if re.search("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}$", val):
                                    temp_domain = expression.AND([[(column, '>=', val + ' 00:00:00')],[(column, '<=', val + ' 23:59:59')]])
                                else:
                                    temp_domain = [(column, 'ilike', val)]
                        search_domain = expression.AND([search_domain,temp_domain])
                    else:
                        if re.search("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}$", value):
                            search_domain = expression.AND([search_domain,[(column, '>=', value + ' 00:00:00')]])
                            search_domain = expression.AND([search_domain,[(column, '<=', value + ' 23:59:59')]])
                        else:
                            search_domain = expression.AND([search_domain,[(column, 'ilike', value)]])

        

        # temp_condition = [('ticket_type_id.name', 'ilike', 'regular')]
        # cond1 = [('ticket_type_id.name', 'ilike', 'Scheduled')]

        # temp_condition = expression.OR([temp_condition,cond1])
        # temp_condition = expression.OR([temp_condition,[('ticket_type_id.name', 'ilike', 'Incident')]])
        # temp_condition = expression.OR([temp_condition,[('ticket_type_id.name', 'ilike', 'Equipment')]])
        # temp_condition = expression.OR([temp_condition,[('ticket_type_id.name', 'ilike', 'Equipment')]])
        # temp_condition = expression.OR([temp_condition,[('ticket_type_id.name', 'ilike', 'first')]])

        # search_domain = expression.AND([search_domain,temp_condition])

        # _logger.info('- search_domain:')
        # _logger.info(search_domain)

        tickets_count = request.env['helpdesk.ticket'].sudo().search_count(search_domain);
        tickets = request.env['helpdesk.ticket'].sudo().search(search_domain, order=order, offset=offset, limit=limit);
        
        for ticket in tickets:
            result.append({                
                'id': ticket.id,
                'display_name': ticket.display_name,
                'create_date': ticket.create_date,
                'helpdesk_type': ticket.team_id.name,
                'ticket_type_id': ticket.ticket_type_id.name or '',
                'operating_site': ticket.x_studio_operation_site.name,
                'status': ticket.stage_id.name,
                'last_update': ticket.write_date,
                'company_id': ticket.company_id.name,
                'created_by': ticket.create_uid.name,
            })

        return {
            'data': result,
            'offset': offset,
            'limit': limit,
            'total': tickets_count
        }

    @route(['/ticket/resolved'], type='json', auth="user", website=False)
    def resolve_ticket(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids:
                # stage = request.env['helpdesk.stage'].sudo().search([('name','in',['Closed','Resolved','Completed','Dispatched']),('is_close','=',True), ('team_ids','in',(ticket_id.team_id.id))],limit=1)
                stage = request.env['helpdesk.stage'].sudo().search([('is_close','=',True), ('team_ids','in',(ticket_id.team_id.id))],limit=1)
                if stage:
                    new_ticket = ticket_id.sudo().write({'stage_id': stage.id})
                    result['status'] = 'success'
                    result['message'] = _('The ticket is successfully resolved.')
                else:
                    result['message'] = _('We cannot resolve this ticket at this stage.')
            else:
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['message'] = _('Ticket not found. Please try again.')

        return result

    @route(['/ticket/reset'], type='json', auth="user", website=False)
    def reset_ticket(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }


        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids:
                stage = request.env['helpdesk.stage'].sudo().search([('name','=','New'),('team_ids','in',(ticket_id.team_id.id))],limit=1)
                if stage:
                    new_ticket = ticket_id.sudo().write({'stage_id': stage.id})
                    result['status'] = 'success'
                    result['message'] = _('The ticket has been reset!')
                else:
                    result['message'] = _('Cannot Reset Ticket')
            else:
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['message'] = _('Ticket not found. Please try again.')

        return result

    def _get_ticket_log(self, ticket_id):
        logs = []
        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        # for message in ticket_id.message_ids.sorted(key=lambda r : r.id):
        for message in ticket_id.message_ids.sorted(key=lambda r : r.id, reverse=True):
            if message.message_type in ['comment', 'email']:
                if message.subtype_id:
                    if message.subtype_id.name == "Note" :
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

        return logs

    @route(['/ticket/reply'], type='json', auth="user", website=False)
    def reply_ticket(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)
        message = kwargs.get('message','')

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids:
                if len(message.strip()) > 0:
                    attachments = kwargs.get('attachment',[])
                    attachment_ids = []
                    file_restricted = ""
                    list_file_type = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.png', '.jpg', '.xls', '.csv']
                    for attachment in attachments:
                        filename, file_extension = os.path.splitext(attachment['filename'])
                        if file_extension.lower() not in list_file_type:
                            file_restricted=  file_restricted + filename + ","
                        else:
                            new_attachment = request.env['ir.attachment'].sudo().create({
                                'name': attachment['filename'],
                                'datas': attachment['data'],
                                'store_fname': attachment['filename'],
                                'res_model': 'mail.compose.message',
                            })
                            if new_attachment:
                                attachment_ids.append(new_attachment.id)
                    ticket_id.sudo().message_post(author_id=request.env.user.partner_id.id,message_type='comment',body=message,subtype_xmlid='mail.mt_comment',attachment_ids=attachment_ids)
                    result['value']['logs'] = self._get_ticket_log(ticket_id)
                    result['value']['id'] =  ticket_id.id
                    if file_restricted != "":
                        result['message'] = _(file_restricted + " | Extension not allowed for upload")
                else:
                    result['status'] = 'restricted'
                    result['message'] = _('Please write the message')
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')

        return result

    @route(['/address/operation-site'], type='json', auth="public", website=False)
    def get_operation_site_address(self, **kwargs):
        data = []
        operating_countries = request.env['operating.country'].sudo().search([], order='name asc')
        temp_global_country = {}
        contact_no_login = kwargs.get('no_login',False)
        for o_country in operating_countries:
            metros = []            
            operating_metros = request.env['operating.metros'].sudo().search([('x_operation_country','=',o_country.id)], order='name asc')
            for metro in operating_metros:
                sites = []
                operating_sites = request.env['operating.sites'].sudo().search([('x_operation_metros','=',metro.id)])
                for site in operating_sites:
                    sites.append({
                        'name': 'OFFICE' if site.x_studio_site_type == 'Admin' else site.name,
                        'address': site.x_studio_site_address
                    })
                metros.append({
                    'name': metro.name,
                    'sites': sites
                })

            no_sales_contact = False
            no_support_contact = False
            no_billing_contact = False

            if not o_country.ns_sales_phone and not o_country.ns_sales_email:
                no_sales_contact = True
            if not o_country.ns_support_phone and not o_country.ns_support_email:
                no_support_contact = True
            if not o_country.ns_billing_phone and not o_country.ns_billing_email:
                no_billing_contact = True

            temp_string = "Global"
            if o_country.name.casefold() == temp_string.casefold():
                temp_global_country = {
                    'name': o_country.name,
                    'ns_sales_phone': o_country.ns_sales_phone or '',
                    'ns_sales_email': o_country.ns_sales_email or '',
                    'ns_support_phone': o_country.ns_support_phone or '',
                    'ns_support_email': o_country.ns_support_email or '',
                    'ns_billing_phone': o_country.ns_billing_phone or '',
                    'ns_billing_email': o_country.ns_billing_email or '',
                    'no_sales_contact': no_sales_contact,
                    'no_support_contact': no_support_contact,
                    'no_billing_contact': no_billing_contact,
                    'metros': metros
                }
            else:
                country = {
                    'name': o_country.name,
                    'ns_sales_phone': o_country.ns_sales_phone or '',
                    'ns_sales_email': o_country.ns_sales_email or '',
                    'ns_support_phone': o_country.ns_support_phone or '',
                    'ns_support_email': o_country.ns_support_email or '',
                    'ns_billing_phone': o_country.ns_billing_phone or '',
                    'ns_billing_email': o_country.ns_billing_email or '',
                    'no_sales_contact': no_sales_contact,
                    'no_support_contact': no_support_contact,
                    'no_billing_contact': no_billing_contact,
                    'metros': metros
                }
                data.append(country)

        if temp_global_country:
            data.insert(0, temp_global_country)

        return {
            'data': data,
            'no_login': contact_no_login
        }

    @route(['/search/operation-site'], type='json', auth="public", website=False)
    def search_operation_site_address(self, **kwargs):
        country = portal_helper.get_default_int_value(kwargs.get('country',''),'',0)
        keyword = '%' + kwargs.get('keyword','') + '%' 
        data = []
        search_condition = 'by_id'
        country_ids = []
        metro_ids = []
        site_ids = []
        operating_countries = request.env['operating.country'].sudo()
        contact_no_login = kwargs.get('no_login',False)
        if country > 0:
            operating_countries = request.env['operating.country'].sudo().search([('id','=',country)], order='name asc')
        else:
            search_condition = 'by_keyword'
            query = """
                SELECT
                    c.id AS c_id,
                    m.id AS m_id,
                    s.id AS s_id
                FROM operating_country c
                LEFT JOIN operating_metros m on m.x_operation_country = c.id
                LEFT JOIN operating_sites s on s.x_operation_metros = m.id
                WHERE
                    c.name ilike %s OR
                    m.name ilike %s OR
                    s.name ilike %s OR
                    s.x_studio_site_address ilike %s
            """
            params = (keyword, keyword, keyword, keyword)
            request.env.cr.execute(query, params)
            result = request.env.cr.dictfetchall() 
            for res in result:
                if res['c_id'] not in country_ids:
                    country_ids.append(res['c_id'])

                if res['m_id'] not in metro_ids:
                    metro_ids.append(res['m_id'])

                if res['s_id'] not in site_ids:
                    site_ids.append(res['s_id'])

                operating_countries = request.env['operating.country'].sudo().search([('id','in',country_ids)], order='name asc')

        
        temp_global_country = {}      
        for o_country in operating_countries:
            metros = []
            operating_metros = request.env['operating.metros'].sudo()
            if search_condition == 'by_id':            
                operating_metros = request.env['operating.metros'].sudo().search([('x_operation_country','=',o_country.id)], order='name asc')
            else:
                operating_metros = request.env['operating.metros'].sudo().search([('x_operation_country','=',o_country.id), ('id','in',metro_ids)], order='name asc')

            for metro in operating_metros:
                sites = []
                operating_sites = request.env['operating.sites'].sudo()
                if search_condition == 'by_id':
                    operating_sites = request.env['operating.sites'].sudo().search([('x_operation_metros','=',metro.id)])
                else:
                    operating_sites = request.env['operating.sites'].sudo().search([('x_operation_metros','=',metro.id), ('id','in',site_ids)])
                for site in operating_sites:
                    sites.append({
                        'name': 'OFFICE' if site.x_studio_site_type == 'Admin' else site.name,
                        'address': site.x_studio_site_address
                    })
                metros.append({
                    'name': metro.name,
                    'sites': sites
                })

            no_sales_contact = False
            no_support_contact = False
            no_billing_contact = False

            if not o_country.ns_sales_phone and not o_country.ns_sales_email:
                no_sales_contact = True
            if not o_country.ns_support_phone and not o_country.ns_support_email:
                no_support_contact = True
            if not o_country.ns_billing_phone and not o_country.ns_billing_email:
                no_billing_contact = True

            temp_string = "Global"
            if o_country.name.casefold() == temp_string.casefold():
                temp_global_country = {
                    'name': o_country.name,
                    'ns_sales_phone': o_country.ns_sales_phone or '',
                    'ns_sales_email': o_country.ns_sales_email or '',
                    'ns_support_phone': o_country.ns_support_phone or '',
                    'ns_support_email': o_country.ns_support_email or '',
                    'ns_billing_phone': o_country.ns_billing_phone or '',
                    'ns_billing_email': o_country.ns_billing_email or '',
                    'no_sales_contact': no_sales_contact,
                    'no_support_contact': no_support_contact,
                    'no_billing_contact': no_billing_contact,
                    'metros': metros
                }
            else:
                country = {
                    'name': o_country.name,
                    'ns_sales_phone': o_country.ns_sales_phone or '',
                    'ns_sales_email': o_country.ns_sales_email or '',
                    'ns_support_phone': o_country.ns_support_phone or '',
                    'ns_support_email': o_country.ns_support_email or '',
                    'ns_billing_phone': o_country.ns_billing_phone or '',
                    'ns_billing_email': o_country.ns_billing_email or '',
                    'no_sales_contact': no_sales_contact,
                    'no_support_contact': no_support_contact,
                    'no_billing_contact': no_billing_contact,
                    'metros': metros
                }
                data.append(country)

        if temp_global_country:
            data.insert(0, temp_global_country)

        return {
            'data': data,
            'no_login': contact_no_login
        }
    
    @route(['/fault-report'], type='json', auth="user", website=False)
    def new_fault_report(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        project_id = kwargs.get('project_id',False)
        value = {
            'ticket_type_id': False,
            'partner_id': False,
            'x_studio_operation_site': False,
            'ns_service_id': False,
            'x_studio_requested_service_date': False,
            'description': ''
        }
        data = {
            'partner': [],
            'ticket_type': [],
            'operating_site': self._get_operation_site(allowed_companies),
            'service': [],
            'tags': []
        }
        project = False
        if project_id:
            project = request.env['project.task'].sudo().browse(int(project_id))
            if project:
                value['ns_service_id'] = project_id
                value['partner_id'] = project.partner_id.id
                value['x_studio_operation_site'] = project.x_studio_operation_site.id

                # data['operating_site'] = self._get_operation_site(project.partner_id.id)
                additionalData = {
                    'fromEdit': True,
                    'service_id' : project_id,
                    'is_fault_report': True,
                }                
                data['service'] = self._get_service_id(allowed_companies, project.partner_id.id, project.x_studio_operation_site.id, '', 'new-fault-report-ticket', additionalData)

        # ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('name','=','Type of Fault')],limit=1)
        ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','fault_report')],limit=1)

        temp_ticket_type = False
        for t_type in ticket_types.nrs_ticket_type_ids:
            if t_type.name == "Others":
                temp_ticket_type = {'id': t_type.id,'name': t_type.name}
            else:
                data['ticket_type'].append({'id': t_type.id,'name': t_type.name})

        if temp_ticket_type:
            data['ticket_type'].append(temp_ticket_type)
        
        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name})

        # if len(data['partner']) == 1 and not value['partner_id']:
        #     value['partner_id'] = data['partner'][0]['id']    
        
        return {'data': data, 'value': value}

    @route(['/fault-report/read'], type='json', auth="user", website=False)
    def read_fault_report(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)


        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Fault Report' in ticket_id.team_id.name:
                
                display_name = ticket_id.display_name
                if ticket_id.ns_ticket_subject and ticket_id.ns_ticket_subject != '':
                    display_name = display_name + " : " + ticket_id.ns_ticket_subject
                
                project_id = ticket_id.ns_service_id.id
                temp_name = ticket_id.ns_service_id.name

                if project_id:
                    project = request.env['project.task'].sudo().browse(int(project_id))
                    if project.x_studio_product.ns_capacity_assignation == 'space_id':
                        if project.x_studio_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_space_id.ns_name)
                    elif project.x_studio_product.ns_capacity_assignation == 'breaker_id' or project.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                        if project.x_studio_related_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_related_space_id.ns_name)

                value = {
                    'id': ticket_id.id,
                    'stage': ticket_id.stage_id.name,
                    'is_close': ticket_id.stage_id.is_close,
                    'display_name': display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.name,
                    'ns_designated_company': ticket_id.ns_designated_company.name,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.name,
                    'ns_service_id': temp_name,
                    'description': ticket_id.description,
                    'logs': self._get_ticket_log(ticket_id)
                }
                result['value'] = value
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result

    @route(['/fault-report/edit'], type='json', auth="user", website=False)
    def edit_fault_report(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        result = {
            'status': 'allowed',
            'message': '',
            'value': {},
            'data': {
                'partner': [],
                'ticket_type': [],
                'operating_site': self._get_operation_site(allowed_companies),
                'service': [],
                'tags': []
            }
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Fault Report' in ticket_id.team_id.name:
                                
                value = {
                    'id': ticket_id.id,
                    'display_name': ticket_id.display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.id,
                    'ns_designated_company': ticket_id.ns_designated_company.id,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.id,
                    'ns_service_id': ticket_id.ns_service_id.id,
                    'description': ticket_id.description,
                    'logs': self._get_ticket_log(ticket_id),
                    'ns_ticket_subject': ticket_id.ns_ticket_subject or ''
                }
                result['value'] = value

                ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','fault_report')],limit=1)
                
                temp_ticket_type = False
                for t_type in ticket_types.nrs_ticket_type_ids:
                    if t_type.name == "Others":
                        temp_ticket_type = {'id': t_type.id,'name': t_type.name}
                    else:
                        result['data']['ticket_type'].append({'id': t_type.id,'name': t_type.name})

                if temp_ticket_type:
                    result['data']['ticket_type'].append(temp_ticket_type)

                # for partner in request.env.user.partner_id.x_studio_associated_company:
                #     if partner.id in allowed_companies:
                #         result['data']['partner'].append({'id': partner.id,'name': partner.name})

                
                # result['data']['operating_site'] = self._get_operation_site(allowed_companies)
                additionalData = {
                    'fromEdit': True,
                    'service_id' : ticket_id.ns_service_id.id,
                    'is_fault_report': True,
                }
                result['data']['service'] = self._get_service_id(allowed_companies, ticket_id.ns_designated_company.id, ticket_id.x_studio_operation_site.id, '', 'new-fault-report-ticket', additionalData)
                result['data']['partner'] = self._get_company_id(ticket_id.ns_service_id.id)

                
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result

    @route(['/fault-report/save'], type='json', auth="user", website=False)
    def save_fault_report(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        ticket_type_id = False
        x_studio_operation_site = False
        # ns_service_id = False
        ns_service_id = False
        description = ''        
        ns_ticket_subject = kwargs.get('ns_ticket_subject','')
                
        is_valid = True
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
        
        if is_valid:
            service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
            ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

            if not ns_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'
        
        if is_valid:
            partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
            partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
            if not partner_id:
                is_valid = False
                result['message'] = _('Designated Company is a required field. Please select the Designated Company.')
            else:
                if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    is_valid = False
                    result['message'] = _('You can not access this Designated Company')

        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_type_id',''),'',0)
            ticket_type_id = request.env['helpdesk.ticket.type'].sudo().search([('id','=',ticket)],limit=1)

            if not ticket_type_id:
                is_valid = False
                result['message'] = 'empty_fault_type'

            # else:
            #     if ns_service_id.partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
            #         is_valid = False
            #         result['message'] = _('You can not access this Service ID')

                
        if is_valid:
            description = kwargs.get('description','')
        #     if description.strip() == '':
        #         is_valid = False
        #         result['message'] = _('Please insert the Additional Remark')
        
        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
            ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

            team_id = request.env['helpdesk.team'].sudo().search([
                ('company_id','=',x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id),
                ('name','ilike','Fault Report')
            ], limit=1)

            if team_id:
                if ticket_id:
                    if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Fault Report' in ticket_id.team_id.name:
                        new_ticket = ticket_id.sudo().write({
                            'team_id': team_id.id,
                            'name': "Fault Report",
                            'partner_id': request.env.user.partner_id.id,
                            'partner_email': request.env.user.partner_id.email,
                            'ns_designated_company': partner_id.id,
                            'ticket_type_id': ticket_type_id.id,
                            'company_id': team_id.company_id.id,
                            'x_studio_operation_site': x_studio_operation_site.id,
                            # 'ns_service_id': ns_service_id.id,
                            'ns_service_id':ns_service_id.id,
                            'description': description,
                            'ns_ticket_subject': ns_ticket_subject
                        })

                        if new_ticket:
                            result['status'] = 'success'
                            # result['message'] = _('The form is successfully submited')

                    else:
                        is_valid = False
                        result['message'] = _('You do not have permission to access this record.')
                else:
                    # stage = request.env['helpdesk.stage'].sudo().search([('name','=','New'),('team_ids','in',(team_id.id))],limit=1)
                    new_ticket = request.env['helpdesk.ticket'].sudo().create({
                        'team_id': team_id.id,
                        'name': "Fault Report",
                        'partner_id': request.env.user.partner_id.id,
                        'partner_email': request.env.user.partner_id.email,
                        'ns_designated_company': partner_id.id,
                        'ticket_type_id': ticket_type_id.id,
                        'company_id': team_id.company_id.id,
                        'x_studio_operation_site': x_studio_operation_site.id,
                        # 'ns_service_id': ns_service_id.id,
                        'ns_service_id':ns_service_id.id,
                        'description': description,
                        'ns_ticket_subject': ns_ticket_subject
                        # 'stage_id': stage.id
                    })

                    if new_ticket:                        
                        ticket_name = new_ticket.name + " (#" + str(new_ticket.id) + ")"
                        result['status'] = 'success'
                        result['message'] = _('Your Ticket "%s" was submitted successfully and we will be in touch soon' % ticket_name)

            else:
                is_valid = False
                result['message'] = _('Error. Please contact Service Desk.')
            
                                   

        return result   

    @route(['/site-access'], type='json', auth="user", website=False)
    def new_site_access_ticket(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))

        data = {
            'partner': [],
            'ticket_type': [],
            'operating_site': self._get_operation_site(allowed_companies),
            'service': []
        }

        ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','Site Access')],limit=1)
        for t_type in ticket_types.nrs_ticket_type_ids:
            data['ticket_type'].append({'id': t_type.id,'name': t_type.name})

        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name, 'selected': False})

        # if len(data['partner']) == 1 :
        #     data['partner'][0]['selected'] = True

        return {'data': data}
 
    @route(['/site-access/read'], type='json', auth="user", website=False)
    def read_site_access_ticket(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Site Access' in ticket_id.team_id.name:
                visit_area = []

                # for area in ticket_id.x_studio_visit_area:
                #     visit_area.append(area.ns_name)

                # x_studio_requested_visitor_array = ticket_id.x_studio_requested_visitor.split(", ")
                
                display_name = ticket_id.display_name
                if ticket_id.ns_ticket_subject and ticket_id.ns_ticket_subject != '':
                    display_name = display_name + " : " + ticket_id.ns_ticket_subject

                ns_site_access_detail_ids = []

                for detail in ticket_id.ns_site_access_detail_ids:
                    ns_site_access_detail_ids.append({
                        'detail_id': detail.id,
                        'detail_data': {
                            'ns_site_access_detail_visitor_name': detail.ns_site_access_detail_visitor_name,
                            'ns_site_access_detail_visitor_id_number': detail.ns_site_access_detail_visitor_id_number,
                        }
                    })
                
                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone
                
                project_id = ticket_id.ns_service_id.id
                temp_name = ticket_id.ns_service_id.name

                if project_id:
                    project = request.env['project.task'].sudo().browse(int(project_id))
                    if project.x_studio_product.ns_capacity_assignation == 'space_id':
                        if project.x_studio_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_space_id.ns_name)
                    elif project.x_studio_product.ns_capacity_assignation == 'breaker_id' or project.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                        if project.x_studio_related_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_related_space_id.ns_name)

                value = {
                    'id': ticket_id.id,
                    'stage': ticket_id.stage_id.name,
                    'is_close': ticket_id.stage_id.is_close,
                    'display_name': display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.name,
                    'ns_designated_company': ticket_id.ns_designated_company.name,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.name,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': temp_name,
                    'ns_site_visit_date_start': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_site_visit_date_start, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_site_visit_date_start else '',
                    'ns_site_visit_date_end': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_site_visit_date_end, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_site_visit_date_end else '',
                    # 'x_studio_requested_visitor': ticket_id.x_studio_requested_visitor,
                    # 'x_studio_requested_visitor_array': x_studio_requested_visitor_array,
                    # 'x_studio_requested_visitor_identification_number': ticket_id.x_studio_requested_visitor_identification_number,
                    'visit_area': visit_area,
                    'description': ticket_id.description,
                    'ns_special_visit_area': ticket_id.ns_special_visit_area,
                    'ns_special_visit_area_name': ticket_id.ns_special_visit_area_name,
                    'logs': self._get_ticket_log(ticket_id),
                    'ns_site_access_detail_ids': ns_site_access_detail_ids
                }
                result['value'] = value
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result

    @route(['/site-access/edit'], type='json', auth="user", website=False)
    def edit_site_access_ticket(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        result = {
            'status': 'allowed',
            'message': '',
            'value': {},
            'data': {
                'partner': [],
                'ticket_type': [],
                'operating_site': self._get_operation_site(allowed_companies),
                'service': [],
                'areas': []
            }
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Site Access' in ticket_id.team_id.name:
                visit_area = []
                # for area in ticket_id.x_studio_visit_area:
                #     visit_area.append({'id': area.id, 'name': area.ns_name})
                
                # x_studio_requested_visitor_array = ticket_id.x_studio_requested_visitor.split(", ")

                ns_site_access_detail_ids = []

                for detail in ticket_id.ns_site_access_detail_ids:
                    ns_site_access_detail_ids.append({
                        'detail_id': detail.id,
                        'detail_data': {
                            'ns_site_access_detail_visitor_name': detail.ns_site_access_detail_visitor_name,
                            'ns_site_access_detail_visitor_id_number': detail.ns_site_access_detail_visitor_id_number,
                        }
                    })

                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone

                value = {
                    'id': ticket_id.id,
                    'display_name': ticket_id.display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.id,
                    'ns_designated_company': ticket_id.ns_designated_company.id,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.id,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': ticket_id.ns_service_id.id,
                    'ns_site_visit_date_start': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_site_visit_date_start, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_site_visit_date_start else '',
                    'ns_site_visit_date_end': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_site_visit_date_end, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_site_visit_date_end else '',
                    # 'x_studio_requested_visitor': ticket_id.x_studio_requested_visitor,
                    # 'x_studio_requested_visitor_array': x_studio_requested_visitor_array,
                    # 'x_studio_requested_visitor_array_length': len(x_studio_requested_visitor_array),
                    # 'x_studio_requested_visitor_identification_number': ticket_id.x_studio_requested_visitor_identification_number,
                    'visit_area': visit_area,
                    'description': ticket_id.description,
                    'logs': self._get_ticket_log(ticket_id),
                    'ns_special_visit_area': ticket_id.ns_special_visit_area,
                    'ns_special_visit_area_name': ticket_id.ns_special_visit_area_name,
                    'ns_ticket_subject': ticket_id.ns_ticket_subject or '',
                    'ns_site_access_detail_ids': ns_site_access_detail_ids
                }
                result['value'] = value
                ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','Site Access')],limit=1)
                for t_type in ticket_types.nrs_ticket_type_ids:
                     result['data']['ticket_type'].append({'id': t_type.id,'name': t_type.name})

                # for partner in request.env.user.partner_id.x_studio_associated_company:
                #     if partner.id in allowed_companies:
                #         result['data']['partner'].append({'id': partner.id,'name': partner.name})

                
                # result['data']['operating_site'] = self._get_operation_site(ticket_id.ns_designated_company.id)
                additionalData = {
                    'fromEdit': True,
                    'service_id' : ticket_id.ns_service_id.id,
                }
                result['data']['service'] = self._get_service_id(allowed_companies, ticket_id.ns_designated_company.id, ticket_id.x_studio_operation_site.id, '', False, additionalData)
                result['data']['partner'] = self._get_company_id(ticket_id.ns_service_id.id)

                # areas = self._get_area(ticket_id.x_studio_operation_site)
                # for area in areas:                    
                #     result['data']['areas'].append({'id': area['id'], 'name': area['name'], 'selected': True if area['id'] in ticket_id.x_studio_visit_area.ids else False})

            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result

    @route(['/site-access/save'], type='json', auth="user", website=False)
    def save_site_access(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        ticket_type_id = False
        x_studio_operation_site = False
        ns_service_id = False
        ns_site_visit_date_start = False
        ns_site_visit_date_end = False
        # x_studio_requested_visitor = False
        # x_studio_requested_visitor_identification_number = False
        x_studio_visit_area = False
        description = ''        
        ns_special_visit_area = kwargs.get('ns_special_visit_area','no')       
        ns_special_visit_area_name = ''  
        ns_ticket_subject = kwargs.get('ns_ticket_subject','')
        osite_timezone='+00:00'
        
        is_valid = True
        
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
            else:
                osite_timezone = x_studio_operation_site.ns_timezone
        
        if is_valid:
            service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
            ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

            if not ns_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'
            # else:
            #     if ns_service_id.partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
            #         is_valid = False
            #         result['message'] = _('You can not access this Service ID')

        if is_valid:
            partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
            partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
            if not partner_id:
                is_valid = False
                result['message'] = _('Designated Company is a required field. Please select the Designated Company.')
            else:
                if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    is_valid = False
                    result['message'] = _('You can not access this Designated Company')

        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_type_id',''),'',0)
            ticket_type_id = request.env['helpdesk.ticket.type'].sudo().search([('id','=',ticket)],limit=1)

            if not ticket_type_id:
                is_valid = False
                result['message'] = 'empty_visit_type'

        if is_valid:
            ns_site_visit_date_start = kwargs.get('ns_site_visit_date_start','')
            ns_site_visit_date_end = kwargs.get('ns_site_visit_date_end','')

            if not portal_helper.check_date_format(ns_site_visit_date_start,'%Y-%m-%d %H:%M'):
                is_valid = False
                result['message'] = 'invalid_date_format'            
            elif not portal_helper.check_date_format(ns_site_visit_date_end,'%Y-%m-%d %H:%M'):
                is_valid = False
                result['message'] = 'invalid_date_format'
        
        if is_valid:
            if ns_special_visit_area == 'yes':
                ns_special_visit_area_name = kwargs.get('ns_special_visit_area_name','')  
                if ns_special_visit_area_name.strip() == '':
                    is_valid = False
                    result['message'] = _("Visit Area is a required field. Please enter the Visit Area Name.")

        if is_valid:
            ns_site_visit_date_start = portal_helper.timezone_adjust(ns_site_visit_date_start, '%Y-%m-%d %H:%M', osite_timezone)
            ns_site_visit_date_end = portal_helper.timezone_adjust(ns_site_visit_date_end, '%Y-%m-%d %H:%M', osite_timezone)

        # if is_valid:
        #     x_studio_requested_visitor = kwargs.get('x_studio_requested_visitor','')
        #     if x_studio_requested_visitor.strip() == '':
        #         is_valid = False
        #         result['message'] = 'empty_visitor_name'


        # if is_valid:
        #     x_studio_requested_visitor_identification_number = kwargs.get('x_studio_requested_visitor_identification_number','')
        #     if x_studio_requested_visitor_identification_number.strip() == '':
        #         is_valid = False
        #         result['message'] = _("Please insert the Requested Visitor Identification Number")

        # if is_valid:
        #     if len(kwargs.get('visit_area',[])) <= 0:
        #         is_valid = False
        #         result['message'] = _('Please select the Visit Area')
        #     else:
        #         x_studio_visit_area = [[6,False,kwargs.get('visit_area',[])]]

        if is_valid:
            description = kwargs.get('description','')
        #     if description.strip() == '':
        #         is_valid = False
        #         result['message'] = _('Please insert the Additional Remark')
        if is_valid:
            invalid_access_detail = kwargs.get('invalid_access_detail',[])
            if invalid_access_detail:
                is_valid = False
                result['message'] = _('Invalid Site Access detail!')
        
        if is_valid:
            temp_access_detail = kwargs.get('temp_access_detail',[])
            if len(temp_access_detail)<1:
                is_valid = False
                result['message'] = _('Site Acces detail must have at least one visitor!')
              
        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
            ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

            team_id = request.env['helpdesk.team'].sudo().search([
                ('company_id','=',x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id),
                ('name','ilike','Site Access')
            ], limit=1)

            if team_id:
                if ticket_id:
                    if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Site Access' in ticket_id.team_id.name:
                        
                        temp_ticket_detail = []
                    
                        temp_detail_data = kwargs.get('temp_access_detail',[])
                        deleted_detail_data = kwargs.get('deleted_access_detail',[])

                        for data in temp_detail_data:
                            if data['detail_id'] == 'new' :
                                temp_ticket_detail.append((0,0,data['detail_data']))
                            else:                            
                                temp_ticket_detail.append((1,data['detail_id'],data['detail_data']))
                                                    
                        for deleted_data in deleted_detail_data:
                            temp_ticket_detail.append((2,int(deleted_data)))
                        
                        new_ticket = ticket_id.sudo().write({
                            'team_id': team_id.id,
                            'name': "Site Access",
                            'partner_id': request.env.user.partner_id.id,
                            'partner_email': request.env.user.partner_id.email,
                            'ns_designated_company': partner_id.id,
                            'ticket_type_id': ticket_type_id.id,
                            'company_id': team_id.company_id.id,
                            'x_studio_operation_site': x_studio_operation_site.id,
                            'ns_site_visit_date_start': ns_site_visit_date_start,
                            'ns_site_visit_date_end': ns_site_visit_date_end,
                            'ns_service_id': ns_service_id.id,
                            'x_studio_visit_area': x_studio_visit_area,
                            'description': description,
                            'ns_ticket_subject': ns_ticket_subject,
                            'ns_special_visit_area': ns_special_visit_area,
                            'ns_special_visit_area_name': ns_special_visit_area_name,
                            'ns_site_access_detail_ids': temp_ticket_detail
                        })

                        if new_ticket:
                            result['status'] = 'success'
                            result['message'] = _('The form is successfully submited.')

                    else:
                        is_valid = False
                        result['message'] = _('You do not have permission to access this record.')
                else: 
                    # stage = request.env['helpdesk.stage'].sudo().search([('name','=','New'),('team_ids','in',(team_id.id))],limit=1)
                    temp_ticket_detail = []
                
                    temp_detail_data = kwargs.get('temp_access_detail',[])

                    for data in temp_detail_data:
                        if data['detail_id'] == 'new' :
                            temp_ticket_detail.append((0,0,data['detail_data']))
                        else:                            
                            temp_ticket_detail.append((1,data['detail_id'],data['detail_data']))

                    new_ticket = request.env['helpdesk.ticket'].sudo().create({
                        'team_id': team_id.id,
                        'name': "Site Access",
                        'partner_id': request.env.user.partner_id.id,
                        'partner_email': request.env.user.partner_id.email,
                        'ns_designated_company': partner_id.id,
                        'ticket_type_id': ticket_type_id.id,
                        'company_id': team_id.company_id.id,
                        'x_studio_operation_site': x_studio_operation_site.id,
                        'ns_site_visit_date_start': ns_site_visit_date_start,
                        'ns_site_visit_date_end': ns_site_visit_date_end,
                        'ns_service_id': ns_service_id.id,
                        'x_studio_visit_area': x_studio_visit_area,
                        # 'x_studio_requested_visitor': x_studio_requested_visitor,
                        # 'x_studio_requested_visitor_identification_number': x_studio_requested_visitor_identification_number,
                        'description': description,
                        'ns_ticket_subject': ns_ticket_subject,
                        'ns_special_visit_area': ns_special_visit_area,
                        'ns_special_visit_area_name': ns_special_visit_area_name,
                        'ns_site_access_detail_ids': temp_ticket_detail
                        # 'stage_id': stage.id
                    })

                    if new_ticket:                        
                        ticket_name = new_ticket.name + " (#" + str(new_ticket.id) + ")"
                        result['status'] = 'success'
                        result['message'] = _('Your Ticket "%s" was submitted successfully and we will be in touch soon.' % ticket_name)
            else:
                is_valid = False
                result['message'] = _('Invalid Helpdesk Team')                      

        return result


    @route(['/shipment'], type='json', auth="user", website=False)
    def new_shipment_ticket(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        project_id = kwargs.get('project_id',False)
        data = {
            'partner': [],
            'operating_site': self._get_operation_site(allowed_companies),
            'service': [],
            'ticket_type': [],
            'uom': []
        }

        value = {
            'partner_id': False,
            'x_studio_operation_site': False,
            'ns_service_id': False
        }
       
        uom_count = request.env['uom.uom'].sudo().search_count([('category_id.name','=','Weight')])            
        uom = request.env['uom.uom'].sudo().search([('category_id.name','=','Weight')],limit = 3)
        
        for uom in uom:
            data['uom'].append({'id': uom.id,'name': uom.name, 'selected': False})
        if uom_count > 3:
            data['uom'].append({'id': 'other','name': 'show more...', 'selected': False})
        
        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name})

        project = False
        if project_id:
            project = request.env['project.task'].sudo().browse(int(project_id))
            if project:
                value['ns_service_id'] = project_id
                value['partner_id'] = project.partner_id.id
                value['x_studio_operation_site'] = project.x_studio_operation_site.id

                # data['operating_site'] = self._get_operation_site(project.partner_id.id)
                additionalData = False
                if re.search("(?i)cabinet", project.name):
                    additionalData = {
                        'fromEdit': True,
                        'service_id' : project_id,
                    } 
                data['service'] = self._get_service_id(allowed_companies, project.partner_id.id, project.x_studio_operation_site.id, '', False, additionalData)

                team_id = request.env['helpdesk.team'].sudo().search([
                    ('company_id','=',project.x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id),
                    ('name','ilike','Shipment')
                ], limit=1)
                # if team_id:
                #     ticket_types = request.env['helpdesk.ticket.type'].sudo().search([])
                #     for t_type in ticket_types:
                #         if team_id.id in t_type.x_studio_visibility.ids:
                #             data['ticket_type'].append({'id': t_type.id,'name': t_type.name})

        # if len(data['partner']) == 1 and not value['partner_id']:
        #     value['partner_id'] = data['partner'][0]['id']
        

        ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','Shipment')],limit=1)
        for t_type in ticket_types.nrs_ticket_type_ids:
            data['ticket_type'].append({'id': t_type.id,'name': t_type.name})

        return {'data': data, 'value': value}

    @route(['/shipment/read'], type='json', auth="user", website=False)
    def read_shipment_ticket(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Shipment' in ticket_id.team_id.name:
                
                display_name = ticket_id.display_name
                if ticket_id.ns_ticket_subject and ticket_id.ns_ticket_subject != '':
                    display_name = display_name + " : " + ticket_id.ns_ticket_subject

                ns_shipment_detail_ids = []

                for detail in ticket_id.ns_shipment_detail_ids:
                    ns_shipment_detail_ids.append({
                        'detail_id': detail.id,
                        'detail_data': {
                            'ns_shipment_detail_item_number': detail.ns_shipment_detail_item_number,
                            'ns_shipment_detail_dimension': detail.ns_shipment_detail_dimension,
                            'ns_shipment_detail_weight' : detail.ns_shipment_detail_weight,
                            'ns_shipment_detail_tracking_number': detail.ns_shipment_detail_tracking_number,
                            'ns_uom': detail.ns_uom.name,
                            'ns_shipment_detail_dispatched' : False,
                            'ns_shipment_detail_storage_location' : None
                        }
                    })
                
                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone

                project_id = ticket_id.ns_service_id.id
                temp_name = ticket_id.ns_service_id.name

                if project_id:
                    project = request.env['project.task'].sudo().browse(int(project_id))
                    if project.x_studio_product.ns_capacity_assignation == 'space_id':
                        if project.x_studio_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_space_id.ns_name)
                    elif project.x_studio_product.ns_capacity_assignation == 'breaker_id' or project.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                        if project.x_studio_related_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_related_space_id.ns_name)

                value = {
                    'id': ticket_id.id,
                    'stage': ticket_id.stage_id.name,
                    'is_close': ticket_id.stage_id.is_close,
                    'display_name': display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.name,
                    'ns_designated_company': ticket_id.ns_designated_company.name,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.name,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': temp_name,
                    'x_studio_loading_dock_required': ticket_id.x_studio_loading_dock_required,
                    'x_studio_number_of_shipment': ticket_id.x_studio_number_of_shipment,
                    'x_studio_shipment_date': datetime.strftime(ticket_id.x_studio_shipment_date, '%Y-%m-%d') if ticket_id.x_studio_shipment_date else '',
                    # 'ns_shipment_date_start': datetime.strftime(ticket_id.ns_shipment_date_start, '%Y-%m-%d %H:%M') if ticket_id.ns_shipment_date_start else '',
                    # 'ns_shipment_date_end': datetime.strftime(ticket_id.ns_shipment_date_end, '%Y-%m-%d %H:%M') if ticket_id.ns_shipment_date_end else '',
                    'ns_shipment_date_start': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_shipment_date_start, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_shipment_date_start else '',
                    'ns_shipment_date_end': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_shipment_date_end, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_shipment_date_end else '',
                    'x_studio_shipment_tracking_number': ticket_id.x_studio_shipment_tracking_number,
                    'description': ticket_id.description,
                    'ns_courier_company': ticket_id.ns_courier_company if ticket_id.ns_courier_company else '',
                    'logs': self._get_ticket_log(ticket_id),
                    'ns_shipment_detail_ids': ns_shipment_detail_ids,
                    'ns_handling_instruction': ticket_id.ns_handling_instruction,
                }
                result['value'] = value
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result

    @route(['/shipment/edit'], type='json', auth="user", website=False)
    def edit_shipment_ticket(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        result = {
            'status': 'allowed',
            'message': '',
            'value': {},
            'data': {
                'partner': [],
                'ticket_type': [],
                'operating_site': self._get_operation_site(allowed_companies),
                'service': [],
                'uom':[]
            }
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Shipment' in ticket_id.team_id.name:
                
                ns_shipment_detail_ids = []

                for detail in ticket_id.ns_shipment_detail_ids:
                    result['data']['uom'].append({'id': detail.ns_uom.id,'name': detail.ns_uom.name, 'selected': False})
                    ns_shipment_detail_ids.append({
                        'detail_id': detail.id,
                        'detail_data': {
                            'ns_shipment_detail_item_number': detail.ns_shipment_detail_item_number,
                            'ns_shipment_detail_dimension': detail.ns_shipment_detail_dimension,
                            'ns_shipment_detail_weight' : detail.ns_shipment_detail_weight,
                            'ns_shipment_detail_tracking_number': detail.ns_shipment_detail_tracking_number,
                            'ns_uom': detail.ns_uom.id,
                            'ns_shipment_detail_dispatched' : False,
                            'ns_shipment_detail_storage_location' : None
                        }
                    })

                x_studio_shipment_date = ''
                if ticket_id.x_studio_shipment_date:
                    temp_date_time = datetime.combine(ticket_id.x_studio_shipment_date, datetime.min.time())
                    x_studio_shipment_date = datetime.strftime(temp_date_time, '%Y-%m-%d')
                
                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone

                value = {
                    'id': ticket_id.id,
                    'display_name': ticket_id.display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.id,
                    'ns_designated_company': ticket_id.ns_designated_company.id,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.id,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': ticket_id.ns_service_id.id,
                    'x_studio_loading_dock_required': ticket_id.x_studio_loading_dock_required,
                    'x_studio_number_of_shipment': ticket_id.x_studio_number_of_shipment,
                    'x_studio_shipment_date': x_studio_shipment_date,
                    # 'ns_shipment_date_start': datetime.strftime(ticket_id.ns_shipment_date_start, '%Y-%m-%d %H:%M') if ticket_id.ns_shipment_date_start else '',
                    # 'ns_shipment_date_end': datetime.strftime(ticket_id.ns_shipment_date_end, '%Y-%m-%d %H:%M') if ticket_id.ns_shipment_date_end else '',
                    'ns_shipment_date_start': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_shipment_date_start, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_shipment_date_start else '',
                    'ns_shipment_date_end': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_shipment_date_end, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_shipment_date_end else '',
                    'x_studio_shipment_tracking_number': ticket_id.x_studio_shipment_tracking_number,
                    'description': ticket_id.description,
                    'ns_courier_company': ticket_id.ns_courier_company,
                    'logs': self._get_ticket_log(ticket_id),
                    'ns_ticket_subject': ticket_id.ns_ticket_subject or '',
                    'ns_shipment_detail_ids': ns_shipment_detail_ids,
                    'ns_handling_instruction': ticket_id.ns_handling_instruction
                }
                result['value'] = value

                ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','Shipment')],limit=1)
                for t_type in ticket_types.nrs_ticket_type_ids:
                     result['data']['ticket_type'].append({'id': t_type.id,'name': t_type.name})
                # ticket_types = request.env['helpdesk.ticket.type'].sudo().search([])
                # for t_type in ticket_types:
                #     if ticket_id.team_id.id in t_type.x_studio_visibility.ids:
                #         result['data']['ticket_type'].append({'id': t_type.id,'name': t_type.name})                

                # for partner in request.env.user.partner_id.x_studio_associated_company:
                #     if partner.id in allowed_companies:
                #         result['data']['partner'].append({'id': partner.id,'name': partner.name})
                
                # result['data']['operating_site'] = self._get_operation_site(ticket_id.ns_designated_company.id)
                additionalData = {
                    'fromEdit': True,
                    'service_id' : ticket_id.ns_service_id.id,
                }
                # result['data']['uom'] =[]
                uom_count = request.env['uom.uom'].sudo().search_count([('category_id.name','=','Weight')])            
                uom = request.env['uom.uom'].sudo().search([('category_id.name','=','Weight')],limit = 3)
                
                # if len( result['data']['uom'])<=0:
                #     for uom in uom:
                #         result['data']['uom'].append({'id': uom.id,'name': uom.name, 'selected': False})

                if uom_count > 3 or len( result['data']['uom'])>0:
                    result['data']['uom'].append({'id': 'other','name': 'show more...', 'selected': False})

                result['data']['service'] = self._get_service_id(allowed_companies, ticket_id.ns_designated_company.id, ticket_id.x_studio_operation_site.id, '', False, additionalData)                
                result['data']['partner'] = self._get_company_id(ticket_id.ns_service_id.id)
            
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result


    @route(['/shipment/save'], type='json', auth="user", website=False)
    def save_shipment(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        ticket_type_id = False
        x_studio_operation_site = False
        ns_service_id = False
        x_studio_number_of_shipment = False
        x_studio_loading_dock_required = False
        x_studio_shipment_date = False
        x_studio_shipment_tracking_number = ''
        ns_courier_company = ''
        description = ''        
        ns_ticket_subject = kwargs.get('ns_ticket_subject','')
        ns_shipment_date_start = False
        ns_shipment_date_end = False
        ns_handling_instruction = kwargs.get('ns_handling_instruction','')
        osite_timezone='+00:00'
        
        is_valid = True       

        x_studio_loading_dock_required = True if kwargs.get('x_studio_loading_dock_required','') == 'on' else False
        
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)
            
            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
            else:
                osite_timezone = x_studio_operation_site.ns_timezone 
        
        if is_valid:
            service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
            ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

            if not ns_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'
            # else:
            #     if ns_service_id.partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
            #         is_valid = False
            #         result['message'] = _('You can not access this Service ID')

        if is_valid:
            partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
            partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
            if not partner_id:
                is_valid = False
                result['message'] = _('Designated Company is a required field. Please select the Designated Company.')
            else:
                if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    is_valid = False
                    result['message'] = _('You can not access this Designated Company')

        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_type_id',''),'',0)
            ticket_type_id = request.env['helpdesk.ticket.type'].sudo().search([('id','=',ticket)],limit=1)

            if not ticket_type_id:
                is_valid = False
                result['message'] = _('Shipping Type is a required field. Please select the Shipping Type.')

        ###### temporary disabled
        # if is_valid:
        #     x_studio_number_of_shipment = portal_helper.get_default_int_value(kwargs.get('x_studio_number_of_shipment',''),'',0)
        #     if x_studio_number_of_shipment <= 0:
        #         is_valid = False
        #         result['message'] = _('Number of Shipment is a required field. Please enter the Number of Shipment in positive value.')

        if is_valid:
            x_studio_shipment_date = kwargs.get('x_studio_shipment_date','')
            ns_shipment_date_start = kwargs.get('ns_shipment_date_start','')
            ns_shipment_date_end = kwargs.get('ns_shipment_date_end','')
            if x_studio_loading_dock_required:
                if not portal_helper.check_date_format(ns_shipment_date_start,'%Y-%m-%d %H:%M'):
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Shipment Date in yyyy-mm-dd hh:mm format')
                elif not portal_helper.check_date_format(ns_shipment_date_end,'%Y-%m-%d %H:%M'):
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Shipment Date in yyyy-mm-dd hh:mm format')
                x_studio_shipment_date = None

            else:
                if not portal_helper.check_date_format(x_studio_shipment_date,'%Y-%m-%d'):
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Shipment Date in yyyy-mm-dd format')                
                ns_shipment_date_start = None
                ns_shipment_date_end = None

        if is_valid:
            if x_studio_loading_dock_required:
                ns_shipment_date_start = portal_helper.timezone_adjust(ns_shipment_date_start, '%Y-%m-%d %H:%M', osite_timezone)
                ns_shipment_date_end = portal_helper.timezone_adjust(ns_shipment_date_end, '%Y-%m-%d %H:%M', osite_timezone)
                        
        if is_valid:
            ns_courier_company = kwargs.get('ns_courier_company','')
            if ns_courier_company.strip() == '':
                is_valid = False
                result['message'] = _('Please insert the Courier Company')

        ###### temporary disabled
        # if is_valid:
        #     x_studio_shipment_tracking_number = kwargs.get('x_studio_shipment_tracking_number','')
        #     if x_studio_shipment_tracking_number.strip() == '':
        #         is_valid = False
        #         result['message'] = _('Shipment Tracking Number is a required field. Please fill in Shipment Tracking Number.')

        if is_valid:
            description = kwargs.get('description','')
        #     if description.strip() == '':
        #         is_valid = False
        #         result['message'] = _('Please insert the Additional Remark')
        if is_valid:
            invalid_shipment_detail = kwargs.get('invalid_shipment_detail',[])
            if invalid_shipment_detail:
                is_valid = False
                result['message'] = _('Invalid shipment detail!')
        
        if is_valid:
            shipment_detail = kwargs.get('shipment_detail',[])
            if len(shipment_detail)<1:
                is_valid = False
                result['message'] = _('Shipment detail must have at least one item!')
                
        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
            ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)
        
            team_id = request.env['helpdesk.team'].sudo().search([
                ('company_id','=',x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id),
                ('name','ilike','Shipment')
            ], limit=1)
            if team_id:
                if ticket_id:
                    if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Shipment' in ticket_id.team_id.name:
                        
                        temp_ticket_detail = []
                    
                        temp_detail_data = kwargs.get('shipment_detail',[])
                        deleted_detail_data = kwargs.get('deleted_shipment_detail',[])

                        for data in temp_detail_data:
                            if data['detail_id'] == 'new' :
                                temp_ticket_detail.append((0,0,data['detail_data']))
                            else:                            
                                temp_ticket_detail.append((1,data['detail_id'],data['detail_data']))
                        
                        for deleted_data in deleted_detail_data:
                            temp_ticket_detail.append((2,int(deleted_data)))
                            
                        new_ticket = ticket_id.sudo().write({
                            'team_id': team_id.id,
                            'name': "Shipment",
                            'partner_id': request.env.user.partner_id.id,
                            'partner_email': request.env.user.partner_id.email,
                            'ns_designated_company': partner_id.id,
                            'ticket_type_id': ticket_type_id.id,
                            'company_id': team_id.company_id.id,
                            'x_studio_operation_site': x_studio_operation_site.id,
                            'ns_service_id': ns_service_id.id,
                            'x_studio_loading_dock_required': x_studio_loading_dock_required,
                            # 'x_studio_number_of_shipment': x_studio_number_of_shipment,
                            'x_studio_shipment_date': x_studio_shipment_date,
                            # 'x_studio_shipment_tracking_number': x_studio_shipment_tracking_number,
                            'ns_courier_company': ns_courier_company,
                            'description': description,
                            'ns_ticket_subject': ns_ticket_subject,
                            'ns_shipment_detail_ids': temp_ticket_detail,                        
                            'ns_shipment_date_start': ns_shipment_date_start,
                            'ns_shipment_date_end': ns_shipment_date_end,
                            'ns_handling_instruction': ns_handling_instruction
                        })

                        if new_ticket:
                            result['status'] = 'success'
                            result['message'] = _('The form is successfully submited.')
                    else:
                        is_valid = False
                        result['message'] = _('You do not have permission to access this record.')
                else:

                    temp_ticket_detail = []
                    
                    temp_detail_data = kwargs.get('shipment_detail',[])

                    for data in temp_detail_data:
                        if data['detail_id'] == 'new' :
                            temp_ticket_detail.append((0,0,data['detail_data']))
                        else:                            
                            temp_ticket_detail.append((1,data['detail_id'],data['detail_data']))

                    new_ticket = request.env['helpdesk.ticket'].sudo().create({
                        'team_id': team_id.id,
                        'name': "Shipment",
                        'partner_id': request.env.user.partner_id.id,
                        'partner_email': request.env.user.partner_id.email,
                        'ns_designated_company': partner_id.id,
                        'ticket_type_id': ticket_type_id.id,
                        'company_id': team_id.company_id.id,
                        'x_studio_operation_site': x_studio_operation_site.id,
                        'ns_service_id': ns_service_id.id,
                        'x_studio_loading_dock_required': x_studio_loading_dock_required,
                        # 'x_studio_number_of_shipment': x_studio_number_of_shipment,
                        'x_studio_shipment_date': x_studio_shipment_date,
                        # 'x_studio_shipment_tracking_number': x_studio_shipment_tracking_number,
                        'ns_courier_company': ns_courier_company,
                        'description': description,
                        'ns_ticket_subject': ns_ticket_subject,
                        'ns_shipment_detail_ids': temp_ticket_detail,                        
                        'ns_shipment_date_start': ns_shipment_date_start,
                        'ns_shipment_date_end': ns_shipment_date_end,
                        'ns_handling_instruction': ns_handling_instruction
                    })

                    if new_ticket:
                        ticket_name = new_ticket.name + " (#" + str(new_ticket.id) + ")"
                        result['status'] = 'success'
                        result['message'] = _('Your Ticket "%s" was submitted successfully and we will be in touch soon.' % ticket_name)
            else:
                is_valid = False
                result['message'] = _('Invalid Helpdesk Team')

        return result


    @route(['/remote-hands'], type='json', auth="user", website=False)
    def new_remote_hand(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        project_id = kwargs.get('project_id',False)
        value = {
            'ticket_type_id': False,
            'ns_designated_company': False,
            'x_studio_operation_site': False,
            'ns_service_id': False,
            'x_studio_requested_service_date': False,
            'description': ''
        }
        data = {
            'partner': [],
            'ticket_type': [],
            'operating_site': self._get_operation_site(allowed_companies),
            'service': []
        }
        project = False

        if project_id:
            project = request.env['project.task'].sudo().browse(int(project_id))
            if project:
                value['ns_service_id'] = project_id
                value['ns_designated_company'] = project.partner_id.id
                value['x_studio_operation_site'] = project.x_studio_operation_site.id
                # data['operating_site'] = self._get_operation_site(allowed_companies) # param : project.partner_id.id
                additionalData = False
                if re.search("(?i)cabinet", project.name):
                    additionalData = {
                        'fromEdit': True,
                        'service_id' : project_id,
                    } 
                data['service'] = self._get_service_id(allowed_companies, project.partner_id.id, project.x_studio_operation_site.id, '', False, False)

        # ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('name','=','Remote Hands')],limit=1)
        ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','remote_hands')],limit=1)
        for t_type in ticket_types.nrs_ticket_type_ids:
            data['ticket_type'].append({'id': t_type.id,'name': t_type.name})
        
        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name})

        # if len(data['partner']) == 1 and not value['ns_designated_company']:
        #     value['ns_designated_company'] = data['partner'][0]['id']
        
        
        return {'data': data, 'value': value}


    @route(['/remote-hands/read'], type='json', auth="user", website=False)
    def read_remote_hads(self, **kwargs):
        result = {
            'status': 'allowed',
            'message': '',
            'value': {}
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Remote Hands' in ticket_id.team_id.name:
                price = 0                
                p_list = request.env['product.pricelist'].sudo()._get_partner_pricelist_multi(ticket_id.ns_designated_company.ids, company_id=ticket_id.x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id)
                pricelist_id = p_list.get(ticket_id.ns_designated_company.id)
                currency = pricelist_id.currency_id.name
                if ticket_id.ns_service_id.timesheet_product_id:
                    price = pricelist_id.sudo().get_product_price(ticket_id.ns_service_id.timesheet_product_id, 1, ticket_id.ns_designated_company)
                    
                if currency == "USD":
                    temp_currency = _("USD / HOUR")
                elif currency == "IDR":
                    temp_currency = _("IDR / HOUR")
                elif currency == "JPY":
                    temp_currency = _("JPY / HOUR")
                elif currency == "KRW":
                    temp_currency = _("KRW / HOUR")
                elif currency == "CNY":
                    temp_currency = _("CNY / HOUR")
                else:
                    temp_currency = _("%s / HOUR" % currency)

                remote_hand_price =  '' + '{:20,.0f}'.format(price) + ' ' + temp_currency

                display_name = ticket_id.display_name
                if ticket_id.ns_ticket_subject and ticket_id.ns_ticket_subject != '':
                    display_name = display_name + " : " + ticket_id.ns_ticket_subject

                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone

                # Initial name with space id
                project_id = ticket_id.ns_service_id.id
                temp_name = ticket_id.ns_service_id.name

                if project_id:
                    project = request.env['project.task'].sudo().browse(int(project_id))
                    if project.x_studio_product.ns_capacity_assignation == 'space_id':
                        if project.x_studio_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_space_id.ns_name)
                    elif project.x_studio_product.ns_capacity_assignation == 'breaker_id' or project.x_studio_product.ns_capacity_assignation == 'patch_panel_id':
                        if project.x_studio_related_space_id.ns_name:
                            temp_name += " / " + str(project.x_studio_related_space_id.ns_name)

                value = {
                    'id': ticket_id.id,
                    'stage': ticket_id.stage_id.name,
                    'is_close': ticket_id.stage_id.is_close,
                    'display_name': display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.name,
                    'ns_designated_company': ticket_id.ns_designated_company.name,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.name,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': temp_name,
                    # 'x_studio_requested_service_date': datetime.strftime(ticket_id.ns_requested_service_date, '%Y-%m-%d %H:%M') if ticket_id.ns_requested_service_date else '',
                    'x_studio_requested_service_date': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_requested_service_date, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_requested_service_date else '',
                    'description': ticket_id.description,
                    'price': remote_hand_price,
                    'logs': self._get_ticket_log(ticket_id),
                    'total_hours_spent': ticket_id.total_hours_spent
                }
                result['value'] = value
            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')

        return result


    @route(['/remote-hands/edit'], type='json', auth="user", website=False)
    def edit_remote_hand(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        result = {
            'status': 'allowed',
            'message': '',
            'value': {},
            'data': {
                'partner': [],
                'ticket_type': [],
                'operating_site': self._get_operation_site(allowed_companies),
                'service': [],
            }
        }

        ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
        ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)
    

        if ticket_id:
            if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Remote Hands' in ticket_id.team_id.name:          
                
                osite_timezone=ticket_id.x_studio_operation_site.ns_timezone

                value = {
                    'id': ticket_id.id,
                    'display_name': ticket_id.display_name,
                    'ticket_type_id': ticket_id.ticket_type_id.id,
                    'ns_designated_company': ticket_id.ns_designated_company.id,
                    'x_studio_operation_site': ticket_id.x_studio_operation_site.id,
                    'operation_site_timezone': ticket_id.x_studio_operation_site.ns_timezone,
                    'ns_service_id': ticket_id.ns_service_id.id,
                    'x_studio_requested_service_date': portal_helper.timezone_adjust_reverse(datetime.strftime(ticket_id.ns_requested_service_date, '%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M', osite_timezone) if ticket_id.ns_requested_service_date else '',
                    'description': ticket_id.description,
                    'price': '0 '+ _('USD / HOUR'),
                    'logs': self._get_ticket_log(ticket_id),                    
                    'total_hours_spent': ticket_id.total_hours_spent,
                    'ns_ticket_subject': ticket_id.ns_ticket_subject or ''
                }
                result['value'] = value

                ticket_types = request.env['nrs.allowed.ticket.type'].sudo().search([('nrs_type','=','remote_hands')],limit=1)
                for t_type in ticket_types.nrs_ticket_type_ids:
                    result['data']['ticket_type'].append({'id': t_type.id,'name': t_type.name})

                # for partner in request.env.user.partner_id.x_studio_associated_company:
                #     if partner.id in allowed_companies:
                #         result['data']['partner'].append({'id': partner.id,'name': partner.name})

                
                # result['data']['operating_site'] = self._get_operation_site(ticket_id.ns_designated_company.id)
                additionalData = {
                    'fromEdit': True,
                    'service_id' : ticket_id.ns_service_id.id,
                }
                result['data']['service'] = self._get_service_id(allowed_companies, ticket_id.ns_designated_company.id, ticket_id.x_studio_operation_site.id, '', False, additionalData)
                result['data']['partner'] = self._get_company_id(ticket_id.ns_service_id.id)
               

            else:
                result['status'] = 'restricted'
                result['message'] = _('You do not have permission to access this record.')
        else:
            result['status'] = 'restricted'
            result['message'] = _('Ticket not found. Please try again.')


        return result


    @route(['/remote-hands/save'], type='json', auth="user", website=False)
    def save_remote_hand(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        ns_designated_company = False
        ticket_type_id = False
        x_studio_operation_site = False
        ns_service_id = False
        x_studio_requested_service_date= ''
        ns_requested_service_date= ''
        description = ''
        ns_ticket_subject = kwargs.get('ns_ticket_subject','')
        osite_timezone='+00:00'
        
        is_valid = True

        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)
            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
            else:
                osite_timezone = x_studio_operation_site.ns_timezone 

        if is_valid:
            service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
            ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

            if not ns_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'
            # else:
            #     if ns_service_id.partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
            #         is_valid = False
            #         result['message'] = _('You can not access this Service ID')

        if is_valid:
            designated_company = portal_helper.get_default_int_value(kwargs.get('ns_designated_company',''),'',0)
            ns_designated_company = request.env['res.partner'].sudo().search([('id','=',designated_company)],limit=1)

            if not ns_designated_company:
                is_valid = False
                result['message'] = _('Designated Company is a required field. Please select the Designated Company.')
            else:
                if ns_designated_company.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    is_valid = False
                    result['message'] = _('You can not access this Designated Company')

        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_type_id',''),'',0)
            ticket_type_id = request.env['helpdesk.ticket.type'].sudo().search([('id','=',ticket)],limit=1)

            if not ticket_type_id:
                is_valid = False
                result['message'] = 'empty_ticket_id'

        if is_valid:       
            # ns_requested_service_date = kwargs.get('x_studio_requested_service_date','')
            ns_requested_service_date = kwargs.get('x_studio_requested_service_date','')
            x_studio_requested_service_date = ns_requested_service_date[0:10]
            if ticket_type_id.name == "Regular Remote Hands":
                if ns_requested_service_date == '' or not ns_requested_service_date:
                    ns_requested_service_date = kwargs.get('default_requested_date','')
                    x_studio_requested_service_date = ns_requested_service_date[0:10]
            else:
                if ns_requested_service_date == '' or not ns_requested_service_date:
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')
                elif not portal_helper.check_date_format(ns_requested_service_date,'%Y-%m-%d %H:%M'):
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')

        if is_valid:
            ns_requested_service_date = portal_helper.timezone_adjust(ns_requested_service_date, '%Y-%m-%d %H:%M', osite_timezone)

        if is_valid:
            description = kwargs.get('description','')

        # is_valid = False
        # result['message'] = _('dev break') 
        
        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_id',''),'',0)
            ticket_id = request.env['helpdesk.ticket'].sudo().browse(ticket)

            team_id = request.env['helpdesk.team'].sudo().search([
                ('company_id','=',x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id),
                ('name','ilike','Remote Hands')
            ], limit=1)
            if team_id:
                if ticket_id:
                    if ticket_id.partner_id.id == request.env.user.partner_id.id and ticket_id.ns_designated_company.id in request.env.user.partner_id.x_studio_associated_company.ids and 'Remote Hands' in ticket_id.team_id.name:
                        new_ticket = ticket_id.sudo().write({
                            'team_id': team_id.id,
                            'name': "Remote Hands",
                            'partner_id': request.env.user.partner_id.id,
                            'ns_designated_company': ns_designated_company.id,
                            'partner_email': request.env.user.partner_id.email,
                            'ticket_type_id': ticket_type_id.id,
                            'company_id': team_id.company_id.id,
                            'x_studio_operation_site': x_studio_operation_site.id,
                            'ns_service_id': ns_service_id.id,
                            'x_studio_requested_service_date': x_studio_requested_service_date,
                            'ns_requested_service_date': ns_requested_service_date,
                            'description': description,
                            'ns_ticket_subject': ns_ticket_subject
                        })

                        if new_ticket:
                            ticket_name = "Remote Hands (#" + str(ticket_id.id) + ")"
                            result['status'] = 'success'
                            result['ticket_name'] = ticket_name
                            if ticket_type_id.name == "Regular Remote Hands":
                                # result['message'] = _('Your ticket "%s" was submitted successfully and we will be in touch with you soon.' % ticket_name)
                                result['message'] = 'success_submit_ticket'
                            else:
                                result['message'] = _('Your ticket "%s" was submitted successfully. The Requested Scheduled Maintenance Date you entered will be taken into consideration and our Ops team will contact you to confirm.' % ticket_name)
                    else:
                        is_valid = False
                        result['message'] = _('You do not have permission to access this record.')
                else:
                    # stage = request.env['helpdesk.stage'].sudo().search([('name','=','New'),('team_ids','in',(team_id.id))],limit=1)
                    new_ticket = request.env['helpdesk.ticket'].sudo().create({
                        'team_id': team_id.id,
                        'name': "Remote Hands",
                        'partner_id': request.env.user.partner_id.id,
                        'ns_designated_company': ns_designated_company.id,
                        'partner_email': request.env.user.partner_id.email,
                        'ticket_type_id': ticket_type_id.id,
                        'company_id': team_id.company_id.id,
                        'x_studio_operation_site': x_studio_operation_site.id,
                        'ns_service_id': ns_service_id.id,
                        'x_studio_requested_service_date': x_studio_requested_service_date,
                        'ns_requested_service_date': ns_requested_service_date,
                        'description': description,
                        'ns_ticket_subject': ns_ticket_subject
                        # 'stage_id': stage.id
                    })

                    if new_ticket:
                        ticket_name = new_ticket.name + " (#" + str(new_ticket.id) + ")"
                        result['status'] = 'success'
                        result['ticket_name'] = ticket_name
                        if ticket_type_id.name == "Regular Remote Hands":
                                # result['message'] = _('Your ticket "%s" was submitted successfully and we will be in touch with you soon.' % ticket_name)
                                result['message'] = 'success_submit_ticket'
                        else:
                            result['message'] = _('Your ticket "%s" was submitted successfully. The Requested Scheduled Maintenance Date you entered will be taken into consideration and our Ops team will contact you to confirm.' % ticket_name)
            else:
                is_valid = False
                result['message'] = _('Invalid Helpdesk Team')

        return result

    @route(['/remote-hands/save-check'], type='json', auth="user", website=False)
    def save_form_check_remote_hand(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        ns_designated_company = False
        ticket_type_id = False
        x_studio_operation_site = False
        ns_service_id = False
        x_studio_requested_service_date= ''
        ns_requested_service_date= ''
        description = ''
        ns_ticket_subject = kwargs.get('ns_ticket_subject','')
        
        is_valid = True

        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'        

        if is_valid:
            service_id = portal_helper.get_default_int_value(kwargs.get('ns_service_id',''),'',0)
            ns_service_id = request.env['project.task'].sudo().search([('id','=',service_id)],limit=1)

            if not ns_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'

        if is_valid:
            designated_company = portal_helper.get_default_int_value(kwargs.get('ns_designated_company',''),'',0)
            ns_designated_company = request.env['res.partner'].sudo().search([('id','=',designated_company)],limit=1)

            if not ns_designated_company:
                is_valid = False
                result['message'] = _('Designated Company is a required field. Please select the Designated Company.')
            else:
                if ns_designated_company.id not in request.env.user.partner_id.x_studio_associated_company.ids:
                    is_valid = False
                    result['message'] = _('You can not access this Designated Company')

        if is_valid:
            ticket = portal_helper.get_default_int_value(kwargs.get('ticket_type_id',''),'',0)
            ticket_type_id = request.env['helpdesk.ticket.type'].sudo().search([('id','=',ticket)],limit=1)

            if not ticket_type_id:
                is_valid = False
                result['message'] = 'empty_ticket_id'

        if is_valid:       
            ns_requested_service_date = kwargs.get('x_studio_requested_service_date','')
            x_studio_requested_service_date = ns_requested_service_date[0:10]
            if ticket_type_id.name == "Regular Remote Hands":
                if ns_requested_service_date == '' or not ns_requested_service_date:
                    ns_requested_service_date = kwargs.get('default_requested_date','')
                    x_studio_requested_service_date = ns_requested_service_date[0:10]
            else:
                if ns_requested_service_date == '' or not ns_requested_service_date:
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')
                elif not portal_helper.check_date_format(ns_requested_service_date,'%Y-%m-%d %H:%M'):
                    is_valid = False
                    result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')

        if is_valid:
            result['status'] = 'pass'    

        return result
    
    @route(['/interconnection-service'], type='json', auth="user", website=False)
    def new_interconnection_service(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        data = {
            'operating_site': self._get_operation_site(allowed_companies),
            'partner': [],
            'ticket_type': [],
            'choose_service': [],
            'media_type': [],
            'patch_panel' : [],
            'port' : []
        }
        
        choose_services = request.env['nrs.req.service.selection'].sudo().search([('nrs_selection_type','=','choose_service'), ('nrs_selection_value', 'ilike', 'Cross Connect')])
        for c_service in choose_services:
            data['choose_service'].append({'name': c_service.name,'value': c_service.nrs_selection_value})

        media_types = request.env['nrs.req.service.selection'].sudo().search([('nrs_selection_type','=','media_type')])
        for m_type in media_types:
            data['media_type'].append({'name': m_type.name,'value': m_type.nrs_selection_value})

        patch_panel = request.env['ns.ns_patchpanel'].sudo().search([('ns_stage', '=', 'available')])
        for p_panel in patch_panel:
            data['patch_panel'].append({'name': p_panel.ns_name,'id': p_panel.id})

        port = request.env['ns.ns_ports'].sudo().search([('ns_stage', '=', 'available')])
        for p in port:
            data['port'].append({'name': p.ns_name,'id': p.id})
        
        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name, 'selected': False})

        # if len(data['partner']) == 1 :
        #     data['partner'][0]['selected'] = True
        
        return {'data': data}

    @route(['/interconnection-service/save'], type='json', auth="user", website=False)
    def save_interconnection_service(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        opportunity_id = False
        a_end_service_id = False
        z_end_service_id = False
        x_studio_operation_site = False
        x_studio_service_request_date= ''
        nrs_loa = ''
        mrc_product = ''
        nrc_product = ''
        mrc_price = 0
        nrc_price = 0
        nrs_patch_panel = False
        ns_port_number = False
        order_line_qty = 0
        
        is_valid = True

        choose_service = kwargs.get('choose_service','')
        intra_customer = True if kwargs.get('intra_customer','') == 'on' else False

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        # if not partner_id:
        #     is_valid = False
        #     result['message'] = _('Please select the Designated Company')
        # else:
        #     if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
        #         is_valid = False
        #         result['message'] = _('You can not access this Designated Company')

        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
                
        if is_valid:
            if not intra_customer: 
                mrc_product = kwargs.get('mrc_product','')
                mrc_product_id = request.env['product.product'].sudo().search([('name','=',mrc_product)],limit=1)
                if not mrc_product_id:
                    is_valid = False
                    result['message'] = 'mrc_product_unavailable'
        
        if is_valid:
            nrc_product = kwargs.get('nrc_product','')
            nrc_product_id = request.env['product.product'].sudo().search([('name','=',nrc_product)],limit=1)
            
            if not nrc_product_id:
                is_valid = False
                result['message'] = 'nrc_product_unavailable'


        if is_valid:
            a_end_service = portal_helper.get_default_int_value(kwargs.get('a_end_service_id',''),'',0)
            a_end_service_id = request.env['project.task'].sudo().search([('id','=',a_end_service)],limit=1)

            if not a_end_service_id:
                is_valid = False
                result['message'] = 'empty_a_side_service_id'

        if is_valid:
            z_end_service = portal_helper.get_default_int_value(kwargs.get('z_end_service_id_select',''),'',0)
            z_end_service_id = request.env['project.task'].sudo().search([('id','=',z_end_service)],limit=1)

            if not z_end_service_id:
                is_valid = False
                result['message'] = 'empty_z_side_service_id'  
        
        if is_valid:
            x_studio_service_request_date = kwargs.get('x_studio_service_request_date','')
            if not portal_helper.check_date_format(x_studio_service_request_date,'%Y-%m-%d'):
                is_valid = False
                result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')
        
        if is_valid:
            nrs_loa = kwargs.get('loa','') 
            if len(nrs_loa.strip()) > 0:
                f = magic.Magic(mime=True)
                nime_type = f.from_buffer(base64.b64decode(nrs_loa))
                list_nime = ['application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-powerpoint',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'image/png',
                    'image/jpeg',
                    'application/vnd.ms-excel',
                    'text/csv'
                    ]
                if nime_type not in list_nime:
                    is_valid = False
                    result['message'] = _('Your file extension not allowed for upload')

            # if not intra_customer:
            #     if len(nrs_loa.strip()) <= 0:
            #         is_valid = False
            #         result['message'] = _('Please upload the Letter of Authorization (LOA)')

        # if is_valid:
        #     if 'Connect' in choose_service:           
        #         if a_end_service_id.x_studio_operation_site.id != z_end_service.x_studio_operation_site.id:
        #             is_valid = False
        #             result['message'] = _("The A-End Service ID Operation Site and the Z-End Service ID Operation Site is different")

        # if is_valid:
        #     if intra_customer:            
        #         if a_end_service_id.partner_id.id != z_end_service.partner_id.id:
        #             is_valid = False
        #             result['message'] = _("The A-End Service ID Customer and the Z-End Service ID Customer is different")
        
        if is_valid:            
            nrs_patch_panel = portal_helper.get_default_int_value(kwargs.get('nrs_patch_panel_id',''),'',0)
            ns_port_number = portal_helper.get_default_int_value(kwargs.get('ns_port_number',''),'',0)
            nrs_patch_panel_id = request.env['ns.ns_patchpanel'].sudo().search([('id','=',nrs_patch_panel)],limit=1)
            ns_port_number_id = request.env['ns.ns_ports'].sudo().search([('id','=',ns_port_number)],limit=1)
            order_line_qty = kwargs.get('quantity',1)

        if is_valid:
            new_name = '-SPO'
            old_orders = request.env['sale.order'].sudo().search([('partner_id','=',partner_id.id), ('name','ilike',a_end_service_id.sale_line_id.order_id.name), ('name','ilike',new_name)])
            new_name += str(len(old_orders)+1)

            temp_order_line = [
                (0,0,{'product_id': nrc_product_id.id, 'product_uom_qty': order_line_qty, 'product_uom': nrc_product_id.uom_id.id})
            ]
            if not intra_customer: 
                # if a_end_service_id.partner_id.id == z_end_service.partner_id.id:
                temp_order_line.append((0,0,{
                    'product_id': mrc_product_id.id,
                    'product_uom_qty': order_line_qty,
                    'product_uom': mrc_product_id.uom_id.id,
                    'nrs_patch_panel_id': nrs_patch_panel_id.id if nrs_patch_panel_id else False,
                    'ns_port_number': ns_port_number_id.id if ns_port_number_id else False,
                    'nrs_a_end_service_id': a_end_service_id.id,
                    'nrs_z_end_service_id': z_end_service_id.id,
                    'nrs_loa': nrs_loa,}))

            
            _logger.info('>>>>>>>>>>>>>>>>>> save_interconnection_service()')

            values = {
                'name': a_end_service_id.sale_line_id.order_id.name + new_name,
                'partner_id': partner_id.id,
                'x_studio_quote_contact_1': request.env.user.partner_id.id,
                'opportunity_id': a_end_service_id.sale_line_id.order_id.opportunity_id.id,
                'user_id': a_end_service_id.sale_line_id.order_id.user_id.id,
                'team_id': a_end_service_id.sale_line_id.order_id.team_id.id,
                'company_id': x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id,
                'nrs_a_end_service_id': a_end_service_id.id,
                'nrs_z_end_service_id': z_end_service_id.id,
                'x_studio_operation_site': x_studio_operation_site.id,
                'x_studio_operation_country': x_studio_operation_site.x_studio_country.id,
                'x_studio_operation_metro': x_studio_operation_site.x_operation_metros.id,
                'x_studio_service_request_date': x_studio_service_request_date,
                'nrs_loa': nrs_loa,
                'approval_state': 'approved',
                'order_line': temp_order_line,
                'crd_contract_required': False,
                'nrs_patch_panel_id': nrs_patch_panel_id.id if nrs_patch_panel_id else False,
                'ns_port_number': ns_port_number_id.id if ns_port_number_id else False,
            }

            order = request.env['sale.order'].sudo().create(values)
            if order:
                order.sudo().name = a_end_service_id.sale_line_id.order_id.name + new_name   
                # order.sudo().update_prices()    
                order.sudo().action_confirm()
                ticket_name = a_end_service_id.sale_line_id.order_id.name + new_name
                result['status'] = 'success'
                result['message'] = _('Your Order "%s" is successfully submitted and will begin provisioning. The Requested Delivery Date that you put will be taken into consideration and our Ops team will contact you further to confirm the Delivery Date' % ticket_name)     
            

        return result

    @route(['/interconnection-service/save-check'], type='json', auth="user", website=False)
    def save_form_check_interconnection_service(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        opportunity_id = False
        a_end_service_id = False
        z_end_service_id = False
        x_studio_operation_site = False
        x_studio_service_request_date= ''
        nrs_loa = ''
        mrc_product = ''
        nrc_product = ''
        mrc_price = 0
        nrc_price = 0
        nrs_patch_panel_id = False
        ns_port_number = False
        order_line_qty = 0
        
        is_valid = True

        choose_service = kwargs.get('choose_service','')
        intra_customer = True if kwargs.get('intra_customer','') == 'on' else False

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)     
         
        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'
        
        if is_valid:
            if not intra_customer: 
                mrc_product = kwargs.get('mrc_product','')
                mrc_product_id = request.env['product.product'].sudo().search([('name','=',mrc_product)],limit=1)
                if not mrc_product_id:
                    is_valid = False
                    result['message'] = 'mrc_product_unavailable'

        if is_valid:
            nrc_product = kwargs.get('nrc_product','')
            nrc_product_id = request.env['product.product'].sudo().search([('name','=',nrc_product)],limit=1)
            
            if not nrc_product_id:
                is_valid = False
                result['message'] = 'nrc_product_unavailable'

        if is_valid:
            a_end_service = portal_helper.get_default_int_value(kwargs.get('a_end_service_id',''),'',0)
            a_end_service_id = request.env['project.task'].sudo().search([('id','=',a_end_service)],limit=1)

            if not a_end_service_id:
                is_valid = False
                result['message'] = 'empty_a_side_service_id'
        
        if is_valid:
            z_end_service = portal_helper.get_default_int_value(kwargs.get('z_end_service_id_select',''),'',0)
            z_end_service_id = request.env['project.task'].sudo().search([('id','=',z_end_service)],limit=1)

            if not z_end_service_id:
                is_valid = False
                result['message'] = 'empty_z_side_service_id'       
        
        if is_valid:
            x_studio_service_request_date = kwargs.get('x_studio_service_request_date','')
            if not portal_helper.check_date_format(x_studio_service_request_date,'%Y-%m-%d'):
                is_valid = False
                result['message'] = _('Invalid date format. Please enter the Requested Delivery Date in yyyy-mm-dd format.')

        if is_valid:
            nrs_loa = kwargs.get('loa','') 
        
        if is_valid:
            nrs_patch_panel_id = portal_helper.get_default_int_value(kwargs.get('nrs_patch_panel_id',''),'',0)
            ns_port_number = portal_helper.get_default_int_value(kwargs.get('ns_port_number',''),'',0)
            order_line_qty = kwargs.get('quantity',1)

        if is_valid:
            result['status'] = 'pass'

        return result

    @route(['/colocation-accessories'], type='json', auth="user", website=False)
    def new_colocation_accessories(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        data = {
            'operating_site': self._get_operation_site(allowed_companies),
            'partner': [],
            'product': [],
        }

        # for partner in request.env.user.partner_id.x_studio_associated_company:
        #     if partner.id in allowed_companies:
        #         data['partner'].append({'id': partner.id,'name': partner.name, 'selected': False})

        # if len(data['partner']) == 1 :
        #     data['partner'][0]['selected'] = True

        products = request.env['product.template'].sudo().search([('x_studio_can_be_sold_in_portal','=',True)])
        for product in products:
            data['product'].append({'id': product.id,'name': product.name})        

        return {'data': data}

    @route(['/colocation_accessories/save'], type='json', auth="user", website=False)
    def save_colocation_accessories(self, **kwargs):
        result = {
            'status': 'failed',
            'message': ''
        }

        partner_id = False
        product_template_id = False
        opportunity_id = False
        x_studio_operation_site = False
        a_end_service_id = False
        x_studio_service_request_date = False

        is_valid = True

        partner = portal_helper.get_default_int_value(kwargs.get('partner_id',''),'',0)
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner)],limit=1)
        # if not partner_id:
        #     is_valid = False
        #     result['message'] = _('Please select the Designated Company')
        # else:
        #     if partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
        #         is_valid = False
        #         result['message'] = _('You can not access this Designated Company')


        if is_valid:
            product = portal_helper.get_default_int_value(kwargs.get('product_id',''),'',0)
            product_template_id = request.env['product.template'].sudo().search([('id','=',product)],limit=1)
            if not product_template_id:
                is_valid = False
                result['message'] = _('Product is a required field. Please select the Product.')


        if is_valid:
            o_site = portal_helper.get_default_int_value(kwargs.get('x_studio_operation_site',''),'',0)
            x_studio_operation_site = request.env['operating.sites'].sudo().search([('id','=',o_site)],limit=1)

            if not x_studio_operation_site:
                is_valid = False
                result['message'] = 'empty_osite'


        if is_valid:
            a_end_service = portal_helper.get_default_int_value(kwargs.get('a_end_service_id',''),'',0)
            a_end_service_id = request.env['project.task'].sudo().search([('id','=',a_end_service)],limit=1)

            if not a_end_service_id:
                is_valid = False
                result['message'] = 'empty_service_id'
            # else:
            #     if a_end_service_id.partner_id.id not in request.env.user.partner_id.x_studio_associated_company.ids:
            #         is_valid = False
            #         result['message'] = _('You can not access this Service ID')

        if is_valid:
            commitment_date = kwargs.get('commitment_date','')
            if not portal_helper.check_date_format(commitment_date,'%Y-%m-%d'):
                is_valid = False
                result['message'] = _('Please insert the Requested Delivery Date with yyyy-mm-dd format')

        if is_valid:
            qty = portal_helper.get_default_int_value(kwargs.get('qty',''),'',0)
            if qty <= 0:
                is_valid = False
                result['message'] = _('Quantity is a required field. Please enter the Quantity in positive value.')


        if is_valid:
            new_name = '-SPO'
            old_orders = request.env['sale.order'].sudo().search([('partner_id','=',partner_id.id), ('name','ilike',a_end_service_id.sale_line_id.order_id.name), ('name','ilike',new_name)])
            new_name += str(len(old_orders)+1)

            values = {
                'name': a_end_service_id.sale_line_id.order_id.name + new_name,
                'partner_id': partner_id.id,
                'x_studio_quote_contact_1': request.env.user.partner_id.id,
                'opportunity_id': a_end_service_id.sale_line_id.order_id.opportunity_id.id,
                'user_id': a_end_service_id.sale_line_id.order_id.user_id.id,
                'team_id': a_end_service_id.sale_line_id.order_id.team_id.id,
                'company_id': x_studio_operation_site.x_studio_country.x_studio_related_digital_edge_companies.id,
                'nrs_a_end_service_id': a_end_service_id.id,
                'x_studio_operation_site': x_studio_operation_site.id,
                'x_studio_operation_country': x_studio_operation_site.x_studio_country.id,
                'x_studio_operation_metro': x_studio_operation_site.x_operation_metros.id,
                'commitment_date': commitment_date,
                'x_studio_service_request_date': commitment_date,
                'approval_state': 'approved',
                'order_line': [
                    (0,0,{'product_id': product_template_id.product_variant_id.id, 'product_uom_qty': qty, 'product_uom': product_template_id.uom_id.id})
                ],
                'crd_contract_required': False
            }

            order = request.env['sale.order'].sudo().create(values)
            if order:
                order.sudo().update_prices()    
                order.sudo().action_confirm()                 
                ticket_name = order.name
                result['status'] = 'success'
                result['message'] = _('Your Order "%s" is successfully submitted and will begin provisioning. The Requested Delivery Date that you put will be taken into consideration and our Ops team will contact you further to confirm the Delivery Date' % ticket_name)     



        return result
    
    @route(['/chek-form/interconnection-services'], type='json', auth="user", website=False)
    def check_interconnection_services_form(self, **kwargs):
        is_a_z_service_same_partner = False
        is_intra_customer = kwargs.get('is_intra_customer')

        a_end_service = portal_helper.get_default_int_value(kwargs.get('service_id',''),'',0)
        a_end_service_id = request.env['project.task'].sudo().search([('id','=',a_end_service)],limit=1)

        if is_intra_customer:            
            z_end_service = portal_helper.get_default_int_value(kwargs.get('z_service_id',''),'',0)
            z_end_service_id  = request.env['project.task'].sudo().search([('id','=',z_end_service)],limit=1)
        else:
            z_end_service = kwargs.get('z_service_id','')
            z_end_service_id  = request.env['project.task'].sudo().search([('ns_service_id','=',z_end_service)])

        if a_end_service_id.partner_id.id == z_end_service_id.partner_id.id:
            is_a_z_service_same_partner = True

        result = {
            'a_z_service_same_partner': is_a_z_service_same_partner,
        }
        return result

    @route(['/get/uom'], type='json', auth="user", website=False)
    def get_uom_id(self, **kwargs):
        additionalData = kwargs.get('additionalData',False)
        data = []       

        uom_count = request.env['uom.uom'].sudo().search_count([('category_id.name','=','Weight')])            
        uom = request.env['uom.uom'].sudo().search([('category_id.name','=','Weight')],limit = 3)
        
        for p in uom:
            data.append({'id': p.id,'name': p.name, 'selected': False})
        
        if uom_count > 3:
            data.append({'id': 'other','name': 'show more...', 'selected': False})

        if additionalData:
            if 'fromPopup' in additionalData:
                data.insert(0, {'id': additionalData['uom_id'],'name': additionalData['uom_name'], 'selected': True})
        
        return {'data': data}
    
    @route(['/get/uom-popup'], type='json', auth="user", website=False)
    def get_uom_id_popup(self, **kwargs):
            
        offset = kwargs['offset']
        limit = kwargs['limit']
        data = [] 
        total = 0  

        uom_count = request.env['uom.uom'].sudo().search_count([('category_id.name','=','Weight')])            
        uom = request.env['uom.uom'].sudo().search([('category_id.name','=','Weight')], limit = limit, offset = offset)

        total = uom_count
        
        for p in uom:
            data.append({'id': p.id,'name': p.name, 'selected': False})
        
        return {'data': data, 'limit' : limit, 'offset' : offset, 'total' : total}