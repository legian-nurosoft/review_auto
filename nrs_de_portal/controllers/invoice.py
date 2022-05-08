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
_logger = logging.getLogger(__name__)


class OrderPortal(Controller):

    @route(['/invoice'], type='json', auth="user", website=False)
    def get_invoice(self, **kwargs):
        _logger.info(">>>>>>>>>>>>>>>>>>>>>> /invoice::get_invoice")
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        order = kwargs['order']  
        offset = kwargs['offset']
        limit = kwargs['limit']
        total = 0
        search_term = kwargs.get('search_term',False)
        data = []

        user_company = request.env.user.company_id

        # company_list = request.env['res.company'].sudo().search()
        
        # _logger.info("- company list:")
        # for company in company_list:
        #     _logger.info("- company id: ")
        #     _logger.info(user_company)


        query = """
            SELECT
                sub.id,
                sub.invoice_number,
                sub.ref,
                sub.invoice_date,
                sub.invoice_date_due,
                sub.payment_state,
                sub.amount_total,
                sub.amount_residual,
                sub.company,                
                sub.order_number,
                sub.currency_name,                
                count(sub.id) OVER() AS total_count
            FROM (
                SELECT DISTINCT ON (move.id)
                    move.id,
                    move.name AS invoice_number,
                    move.ref,
                    move.invoice_date,
                    move.invoice_date_due,
                    move.payment_state,
                    move.amount_total,
                    move.amount_residual,
                    partner.name AS company,                
                    s_order.name AS order_number,
                    currency.name AS currency_name
                FROM account_move move
                LEFT JOIN res_partner AS partner ON partner.id = move.partner_id
                LEFT JOIN account_move_line move_line ON move_line.move_id = move.id AND move_line.subscription_id IS NOT NULL
                LEFT JOIN sale_subscription s_subscription ON s_subscription.id = move_line.subscription_id
                LEFT JOIN sale_order s_order ON s_order.id = s_subscription.x_studio_original_sales_order
                LEFT JOIN res_currency currency ON currency.id = move.currency_id
                WHERE 
                    move.partner_id in %s AND
                    move.move_type in ('out_invoice', 'out_refund') AND
                    move.state = %s
        """
        

        if search_term != False:
            for search_data in search_term.split('|'):
                column = search_data.split('->')[0]
                value = search_data.split('->')[1]

                arrayValue = value.split(' or ')

                if column in ['s_order.name', 'move.name', 'partner.name', 'move.ref']:
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
                elif column in ['move.invoice_date', 'move.invoice_date_due']:
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
            ) sub               
            ORDER BY %s
        """ % order
        query += """
            LIMIT %s
            OFFSET %s
        """ % (limit, offset)
        params = (allowed_companies,'posted')
        _logger.info(query)
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()
        
        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        inv_payment_state = {
            'not_paid': 'Not Paid',
            'in_payment': 'In Payment',
            'paid': 'Paid',
            'partial': 'Partially Paid',
            'reversed': 'Reversed',
            'invoicing_legacy': 'Invoicing App Legacy'
        } 

        if len(result) > 0:
            total = result[0]['total_count']
            for res in result:
                data.append({
                    'id': res['id'],
                    'invoice_number': res['invoice_number'],
                    'ref': res['ref'],
                    'invoice_date': datetime.strftime(res['invoice_date'], '%d/%m/%Y') if res['invoice_date'] else '',
                    'invoice_date_due': datetime.strftime(res['invoice_date_due'], '%d/%m/%Y') if res['invoice_date_due'] else '',
                    'payment_state': inv_payment_state.get(res['payment_state'],''),
                    'amount_total': '{:20,.0f}'.format(res['amount_total']) + ' ' + res['currency_name'],
                    'amount_residual': '{:20,.0f}'.format(res['amount_residual']) + ' ' + res['currency_name'],
                    'company': res['company'],
                    'order_number': res['order_number']
                })

        user_company = request.env.user.company_id
        
        return {
            'data': data, 
            'user_company': user_company.name,
            'offset': offset,
            'limit': limit,
            'total': total
        }


    @route(['/invoice/download'], type='http', auth="user", website=False)
    def download_invoice(self, **kwargs):
        allowed_companies = portal_helper.get_allowed_companies(request.env.user,dict(request.httprequest.cookies).get('acids'))
        order = kwargs['order']
        data = []

        query = """
            SELECT
                sub.id,
                sub.invoice_number,
                sub.ref,
                sub.invoice_date,
                sub.invoice_date_due,
                sub.payment_state,
                sub.amount_total,
                sub.amount_residual,
                sub.company,                
                sub.order_number,
                sub.currency_name
            FROM (
                SELECT DISTINCT ON (move.id)
                    move.id,
                    move.name AS invoice_number,
                    move.ref,
                    move.invoice_date,
                    move.invoice_date_due,
                    move.payment_state,
                    move.amount_total,
                    move.amount_residual,
                    partner.name AS company,                
                    s_order.name AS order_number,
                    currency.name AS currency_name
                FROM account_move move
                JOIN res_partner AS partner ON partner.id = move.partner_id
                LEFT JOIN account_move_line move_line ON move_line.move_id = move.id AND move_line.subscription_id IS NOT NULL
                LEFT JOIN sale_subscription s_subscription ON s_subscription.id = move_line.subscription_id
                LEFT JOIN sale_order s_order ON s_order.id = s_subscription.x_studio_original_sales_order
                LEFT JOIN res_currency currency ON currency.id = move.currency_id
                WHERE 
                    move.partner_id in %s AND
                    move.move_type in ('out_invoice', 'out_refund')
            ) sub
            ORDER BY                 
        """

        query += order
        params = (allowed_companies,)
        request.env.cr.execute(query, params)
        result = request.env.cr.dictfetchall()
        
        tz = 'UTC'
        if request.env.user.tz:
            tz = pytz.timezone(request.env.user.tz)

        inv_payment_state = {
            'not_paid': 'Not Paid',
            'in_payment': 'In Payment',
            'paid': 'Paid',
            'partial': 'Partially Paid',
            'reversed': 'Reversed',
            'invoicing_legacy': 'Invoicing App Legacy'
        }        
        
        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('Invoice.xlsx'))
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

        sheet.write(0, 0, _('No.'), header_style)
        sheet.write(0, 1, _('Invoice Number'), header_style)
        sheet.write(0, 2, _('Company'), header_style)
        sheet.write(0, 3, _('Client Order Reference'), header_style)
        sheet.write(0, 4, _('Order Number'), header_style)
        sheet.write(0, 5, _('Invoice Date'), header_style)
        sheet.write(0, 6, _('Due Date'), header_style)
        sheet.write(0, 7, _('Invoice Status'), header_style)
        sheet.write(0, 8, _('Total Amount'), header_style)
        sheet.write(0, 9, _('Amount Due'), header_style)

        row = 1
        number = 1

        for res in result:
            sheet.write(row, 0, number, text_style)
            sheet.write(row, 1, res['invoice_number'], text_style)
            sheet.write(row, 2, res['company'], text_style)
            sheet.write(row, 3, res['ref'], text_style)
            sheet.write(row, 4, res['order_number'], text_style)
            if res['invoice_date']:
                sheet.write_datetime(row, 5, res['invoice_date'], date_style)
            if res['invoice_date_due']:
                sheet.write_datetime(row, 6, res['invoice_date_due'], date_style)
            sheet.write(row, 7, inv_payment_state.get(res['payment_state'],''), text_style)
            sheet.write(row, 8, '{:20,.0f}'.format(res['amount_total']) + ' ' + res['currency_name'], text_style)
            sheet.write(row, 9, '{:20,.0f}'.format(res['amount_residual']) + ' ' + res['currency_name'], text_style)

            row += 1
            number += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
 
        return response