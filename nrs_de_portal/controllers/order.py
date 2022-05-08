# -*- coding: utf-8 -*-

import base64
import functools
import json
import logging
import math
import re

from werkzeug import urls

from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from datetime import datetime, timedelta
import pytz
import io
import xlsxwriter
from . import portal_helper
import logging
_logger = logging.getLogger(__name__)

class OrderPortal(Controller):

    @route(['/order/under-provisioning'], type='json', auth="user", website=False)
    def order_wip(self, **kwargs):
        order = kwargs['order']
        offset = kwargs['offset']
        limit = kwargs['limit']
        total = 0
        search_term = kwargs.get('search_term',False)
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        data = []
        query = """
            SELECT
                p_task.id, 
                p_task.x_studio_service_id as service_name,
                p_template.name AS product_name,
                COALESCE(o_sites.name,'') AS location_name,
                s_order.create_date AS order_date,
                p_task.x_studio_service_request_date AS request_date,
                p_task_type.name AS status,
                count(p_task.id) OVER() AS total_count
            FROM project_task p_task
            LEFT JOIN project_project p_project ON p_project.id = p_task.project_id
            LEFT JOIN sale_order_line s_line ON s_line.id = p_task.sale_line_id
            LEFT JOIN sale_order s_order ON s_order.id = s_line.order_id
            LEFT JOIN product_product p_product ON p_product.id = s_line.product_id
            LEFT JOIN product_template p_template ON p_template.id = p_product.product_tmpl_id
            LEFT JOIN project_task_type p_task_type ON p_task_type.id = p_task.stage_id
            LEFT JOIN operating_sites o_sites on o_sites.id = p_task.x_studio_operation_site
            WHERE 
                p_task.partner_id in %s AND
                p_project.name ilike %s AND
                p_task_type.name in ('Customer Acceptance','Pending Provisioning', 'Pending Change')
        """   

        if search_term != False:
            for search_data in search_term.split('|'):
                column = search_data.split('->')[0]
                value = search_data.split('->')[1]

                arrayValue = value.split(' or ')

                if column in ['p_task.x_studio_service_id', 'o_sites.name', 'p_template.name', 'p_task_type.name']:
                    if len(arrayValue) > 1:
                        temp_index = 1
                        query += " AND ( "
                        for val in arrayValue:
                            if temp_index <  len(arrayValue):
                                query += column + " ilike '%%" + val + "%%'" + " or "
                            else:
                                query += column + " ilike '%%" + val + "%%'" + " )"
                            temp_index = temp_index + 1
                    else:
                        query += " AND " + column + " ilike '%%" + value + "%%'" 
                elif column in ['s_order.create_date', 'p_task.x_studio_service_request_date']:
                    if len(arrayValue) > 1:
                        temp_index = 1
                        query += " AND ( "
                        for val in arrayValue:
                            if temp_index <  len(arrayValue):
                                query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " or "
                            else:
                                query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " )"
                            temp_index = temp_index + 1
                    else:
                        query += " AND substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + value + "%%'"
        
        query += """            
            ORDER BY %s
        """ % order
        query += """
            LIMIT %s
            OFFSET %s
        """ % (limit, offset)

        params = (allowed_companies, '%Installed Base%')
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()
        
        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)
        if len(result) > 0:
            total = result[0]['total_count']
            for res in result:
                data.append({
                    'id': res['id'],
                    'service_name': res['service_name'],
                    'product_name': res['product_name'],
                    'location_name': res['location_name'],
                    'order_date': datetime.strftime(res['order_date'].astimezone(tz), '%d/%m/%Y'),
                    'status': _(res['status']),
                    'request_date': datetime.strftime(res['request_date'], '%d/%m/%Y') if res['request_date'] else '',
                })

        return {
            'data': data, 
            'offset': offset,
            'limit': limit,
            'total': total
        }


    @route(['/order/installed/summary'], type='json', auth="user", website=False)
    def order_installed_summary(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        
        search_term = kwargs.get('search_term',False)

        temp_company = []
        for companies in allowed_companies:
            if companies != 0:
                temp_company.append(companies)
        
        temp_partner = request.env['res.partner'].sudo().search([["parent_id", "in", temp_company]])

        for partner in temp_partner:
            allowed_companies = allowed_companies + (partner.id,)

        query = """
            SELECT
                p_cat.name AS category,
                COALESCE(o_sites.name,'Undefined') AS location,
                p_cat.nrs_color,
                count(p_task.id) as count
            FROM project_task p_task
            LEFT JOIN project_project p_project ON p_project.id = p_task.project_id
            LEFT JOIN product_category p_cat ON p_cat.id = p_task.x_studio_product_category
            LEFT JOIN operating_sites o_sites on o_sites.id = p_task.x_studio_operation_site
            LEFT JOIN project_task_type p_task_type ON p_task_type.id = p_task.stage_id
            LEFT JOIN sale_order_line s_line ON s_line.id = p_task.sale_line_id
            LEFT JOIN sale_order s_order ON s_order.id = s_line.order_id
            LEFT JOIN product_product p_product ON p_product.id = s_line.product_id
            LEFT JOIN product_template p_template ON p_template.id = p_product.product_tmpl_id
            WHERE 
                p_task.partner_id in %s AND
                p_project.name ilike %s AND
                p_task_type.name in ('In Service')
        """    

        if search_term != False:
            for search_data in search_term.split('|'):
                column = search_data.split('->')[0]
                value = search_data.split('->')[1]

                arrayValue = value.split(' or ')

                if column in ['p_task.x_studio_service_id', 'o_sites.name', 'p_template.name', 's_order.client_order_ref', 's_order.name']:
                    if len(arrayValue) > 1:
                        temp_index = 1
                        query += " AND ( "
                        for val in arrayValue:
                            if temp_index <  len(arrayValue):
                                query += column + " ilike '%%" + val + "%%'" + " or "
                            else:
                                query += column + " ilike '%%" + val + "%%'" + " )"
                            temp_index = temp_index + 1
                    else:
                        query += " AND " + column + " ilike '%%" + value + "%%'" 
                elif column in ['p_task.x_studio_installed_date', 's_order.x_studio_contract_end_date']:
                        if len(arrayValue) > 1:
                            temp_index = 1
                            query += " AND ( "
                            for val in arrayValue:
                                if temp_index <  len(arrayValue):
                                    query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " or "
                                else:
                                    query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " )"
                                temp_index = temp_index + 1
                        else:
                            query += " AND substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + value + "%%'"
        
        query += """
            GROUP BY 
                category,
                location,
                p_cat.nrs_color
        """

        params = (allowed_companies,'%Installed Base%')
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()
        table = []
        location = []
        current_cat = []
        color = []

        if len(result) > 0:
            for res in result:
                if res['location'] not in location:
                    location.append(res['location'])                          

                if res['category'] not in current_cat:
                    color.append(res['nrs_color'])
                    current_cat.append(res['category'])
                    data = {
                        'name': res['category'],
                        'color': res['nrs_color'],
                        'column': []
                    }

                    for loc in result:
                        if res['category'] == loc['category']:
                            is_exist = False
                            index = -1
                            for col in data['column']:
                                index += 1
                                if col['location'] == loc['location']:
                                    is_exist = True
                            
                            if is_exist:
                                data['column'][index]['value'] += loc['count']
                            else:
                                data['column'].append({
                                    'location': loc['location'],
                                    'value': loc['count']
                                })

                    table.append(data)

        
        normalized_table = []
        for t in table:
            temp = []
            temp.append([t['color'],t['name']])
            total = 0
            for loc in location:
                is_exist = False
                for col in t['column']:
                    if col['location'] == loc:
                        temp.append(col['value'])
                        total += col['value']
                        is_exist = True
                if not is_exist:
                    temp.append(0)

            temp.append(total)
            normalized_table.append(temp)

        
        total = []
        for i in range(len(location)+1):
            total.append(0)
            for line in normalized_table:
                total[i] += line[i+1]

        
        chart = []
        index = 0
        for loc in location:
            temp = {
                'label': loc,
                'total': 0,
                'data': [],
                'backgroundColor': color
            }
            for nt in normalized_table:
                temp['data'].append(nt[index+1])
                temp['total'] += nt[index+1]

            chart.append(temp)
            index += 1

        
        return {
            'location': location,
            'table': normalized_table,
            'total': total,
            'chart': chart
        }



    @route(['/order/installed'], type='json', auth="user", website=False)
    def order_installed(self, **kwargs):
        order = kwargs['order']
        # name =  '%' + kwargs['keyword'] + '%'  
        offset = kwargs['offset']
        limit = kwargs['limit']
        total = 0        
        search_term = kwargs.get('search_term',False)
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        data = []

        temp_company = []
        for companies in allowed_companies:
            if companies != 0:
                temp_company.append(companies)
        
        temp_partner = request.env['res.partner'].sudo().search([["parent_id", "in", temp_company]])

        for partner in temp_partner:
            allowed_companies = allowed_companies + (partner.id,)

        query = """
            SELECT 
                p_task.id AS project_task_id,
                p_task.x_studio_service_id AS service_name,
                p_template.default_code AS product_code,
                COALESCE(o_sites.name,'') AS location_name,
                p_template.name AS product_name,
                s_order.x_studio_contract_end_date AS contract_end_date,
                s_order.name AS sales_order_name,
                1 AS qty,
                s_order.client_order_ref AS po_number,
                p_task.x_studio_installed_date AS installed_date,
                count(p_task.id) OVER() AS total_count
            FROM project_task p_task
            LEFT JOIN project_project p_project ON p_project.id = p_task.project_id
            LEFT JOIN sale_order_line s_line ON s_line.id = p_task.sale_line_id
            LEFT JOIN sale_order s_order ON s_order.id = s_line.order_id
            LEFT JOIN product_product p_product ON p_product.id = s_line.product_id
            LEFT JOIN product_template p_template ON p_template.id = p_product.product_tmpl_id
            LEFT JOIN project_task_type p_task_type ON p_task_type.id = p_task.stage_id
            LEFT JOIN operating_sites o_sites on o_sites.id = p_task.x_studio_operation_site
            WHERE 
                p_task.partner_id in %s AND
                p_project.name ilike %s AND
                p_task_type.name in ('In Service')
        """

        if search_term != False:
            for search_data in search_term.split('|'):
                column = search_data.split('->')[0]
                value = search_data.split('->')[1]

                arrayValue = value.split(' or ')

                if column in ['p_task.x_studio_service_id', 'o_sites.name', 'p_template.name', 's_order.client_order_ref', 's_order.name']:
                    if len(arrayValue) > 1:
                        temp_index = 1
                        query += " AND ( "
                        for val in arrayValue:
                            if temp_index <  len(arrayValue):
                                query += column + " ilike '%%" + val + "%%'" + " or "
                            else:
                                query += column + " ilike '%%" + val + "%%'" + " )"
                            temp_index = temp_index + 1
                    else:
                        query += " AND " + column + " ilike '%%" + value + "%%'" 
                elif column in ['p_task.x_studio_installed_date', 's_order.x_studio_contract_end_date']:
                        if len(arrayValue) > 1:
                            temp_index = 1
                            query += " AND ( "
                            for val in arrayValue:
                                if temp_index <  len(arrayValue):
                                    query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " or "
                                else:
                                    query += "substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + val + "%%'" + " )"
                                temp_index = temp_index + 1
                        else:
                            query += " AND substring(cast(" + column + " as varchar), 1, 10) ilike '%%" + value + "%%'"
                        
        
        query += """            
            ORDER BY %s
        """ % order
        query += """
            LIMIT %s
            OFFSET %s
        """ % (limit, offset)
        params = (allowed_companies, '%Installed Base%')
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()   
        
        if len(result) > 0:
            total = result[0]['total_count']    
            for res in result:
                data.append({
                    'project_task_id': res['project_task_id'],
                    'service_name': res['service_name'],
                    'product_code': res['product_code'],
                    'location_name': res['location_name'],
                    'product_name': res['product_name'],
                    'so_name': res['sales_order_name'],
                    'qty': res['qty'],
                    'po_number': res['po_number'],
                    'installed_date': datetime.strftime(res['installed_date'], '%d/%m/%Y') if res['installed_date'] else '',
                    'contract_end_date': datetime.strftime(res['contract_end_date'], '%d/%m/%Y') if res['contract_end_date'] else '',
                })

        return {
            'data': data, 
            'offset': offset,
            'limit': limit,
            'total': total
        }


    @route(['/order/installed/download'], type='http', auth="user", website=False)
    def download_order_installed(self, **kwargs):
        order = kwargs['order']
        name =  '%' + kwargs['keyword'] + '%'  
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        data = []

        query = """
            SELECT 
                p_task.id AS project_task_id,
                p_task.x_studio_service_id AS service_name,
                p_template.default_code AS product_code,
                COALESCE(o_sites.name,'') AS location_name,
                p_template.name AS product_name,
                1 AS qty,
                s_order.client_order_ref AS po_number,
                p_task.x_studio_installed_date AS installed_date,
                s_order.x_studio_contract_end_date AS contract_end_date
            FROM project_task p_task
            LEFT JOIN project_project p_project ON p_project.id = p_task.project_id
            LEFT JOIN sale_order_line s_line ON s_line.id = p_task.sale_line_id
            LEFT JOIN sale_order s_order ON s_order.id = s_line.order_id
            LEFT JOIN product_product p_product ON p_product.id = s_line.product_id
            LEFT JOIN product_template p_template ON p_template.id = p_product.product_tmpl_id
            LEFT JOIN project_task_type p_task_type ON p_task_type.id = p_task.stage_id
            LEFT JOIN operating_sites o_sites on o_sites.id = p_task.x_studio_operation_site
            WHERE 
                p_task.partner_id in %s AND
                p_project.name ilike %s AND
                p_task_type.name in ('In Service') AND
                (
                    p_task.x_studio_service_id ilike %s OR
                    p_template.default_code ilike %s OR
                    o_sites.name ilike %s OR
                    p_template.name ilike %s
                )
            ORDER BY 
        """
        
        query += order
        params = (allowed_companies, '%Installed Base%', name, name, name, name)
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()   
        
        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('Installed Service.xlsx'))
                    ]
                )
 
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True}) 
        
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'center'})
        text_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'left'})
        date_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'left', 'num_format': 'dd/mm/yyyy'})
        
        sheet = workbook.add_worksheet('Installed Service')
        sheet.set_column('A:A', 5)
        sheet.set_column('B:F', 25)

        sheet.write(0, 0, 'No.', header_style)
        sheet.write(0, 1, 'Service ID', header_style)
        sheet.write(0, 2, 'Operation Site', header_style)
        sheet.write(0, 3, 'Product', header_style)
        sheet.write(0, 4, 'Quantity', header_style)
        sheet.write(0, 5, 'Customer Reference Number', header_style)
        sheet.write(0, 6, 'Installed Date', header_style)
        sheet.write(0, 7, 'Contract End Date', header_style)

        row = 1
        number = 1
        
        for res in result:
            sheet.write(row, 0, number, text_style)
            sheet.write(row, 1, res['service_name'], text_style)
            sheet.write(row, 2, res['location_name'], text_style)
            sheet.write(row, 3, res['product_name'], text_style)
            sheet.write(row, 4, res['qty'], text_style)
            sheet.write(row, 5, res['po_number'], text_style)
            if res['installed_date']:
                sheet.write_datetime(row, 6, res['installed_date'], date_style)
            sheet.write_datetime(row, 7, res['contract_end_date'], date_style)

            row += 1
            number += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
 
        return response