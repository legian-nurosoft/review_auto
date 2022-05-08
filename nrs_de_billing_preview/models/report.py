# -*- coding: utf-8 -*-

from odoo import models, api, fields, exceptions, _
from odoo import tools

class BillingPreviewReport(models.AbstractModel):
    _name = "billing.preview.report"
    _description = "Billing Preview"
    _inherit = "account.report"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_partner = True

    @api.model
    def _get_options(self, previous_options=None):        
        options = super(BillingPreviewReport, self)._get_options(previous_options=previous_options)
        options['current_company'] = self.env.company.name

        return options

    def _get_report_name(self):
        return _('Billing Preview')

   
    def _get_columns_name(self, options):
        return [
        	{},
            {'name': _('Sales Order')},
            {'name': _('Start Date')},
            {'name': _('Service Charge Period: From')},
            {'name': _('Service Charge Period: To')},
            {'name': _('Site')},
            {'name': _('Product Code')},
            {'name': _('Description')},
            {'name': _('Qty')},
            {'name': _('Unit')},
            {'name': _('Unit Cost')},
            {'name': _('MRC')},
            {'name': _('NRC')},
            {'name': _('Taxes')},
            {'name': _('Grand Total')}
        ]

    @api.model
    def _get_options_date_domain(self, options):
        def create_date_domain(options_date):
            date_field = 'ns_recurring_next_date'
            domain = [(date_field, '<=', options_date['date_to'])]
            if options_date['mode'] == 'range':
                domain += [(date_field, '>=', options_date['date_from'])]
                    
            return domain

        if not options.get('date'):
            return []
        return create_date_domain(options['date'])

    def _can_see_partner(self, partner, partner_ids, partner_category_ids):
        result = True

        if len(partner_ids) > 0 and partner.id not in partner_ids:
            result = False

        if len(partner_category_ids) > 0:
            category_match = False
            for category in partner.category_id.ids:
                if category in partner_category_ids:
                    category_match = True

            result = category_match

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        if len(self._context.get('allowed_company_ids',[])) > 1:
            raise exceptions.UserError(_('Please select one company only.'))

        result = []
        domain = [('ns_company_id','=',self.env.company.id)]
        date_domain = self._get_options_date_domain(options)

        partner_ids = [int(partner) for partner in options['partner_ids']]
        partner_category_ids = [int(category) for category in options['partner_categories']]

        billings = self.env['ns.billing.preview'].search(domain + date_domain)
        for bill in billings:
            item = {
                'id': bill.id,
                'name': fields.Date().to_string(bill.ns_recurring_next_date),
                'level': 1, 'trust': 'normal', 'unfoldable': True, 'unfolded': None,
                'columns': [
                    {},{},{},{},{},{},{},{},{},{},{},{},{},{}
                ]
            }

            childs = []
            total_qty = 0
            total_cost = 0
            total_mrc = 0
            total_nrc = 0
            total_tax = 0
            grand_total = 0
            last_order_id = 0
            currency = False
            for detail in bill.ns_detail_id:
                if self._can_see_partner(detail.ns_partner_id, partner_ids, partner_category_ids):
                    total_qty += detail.ns_quantity
                    total_cost += detail.ns_price_unit
                    total_mrc += detail.ns_mrc_price_unit
                    total_nrc += detail.ns_nrc_price_unit
                    total_tax += detail.ns_tax
                    grand_total += detail.ns_total
                    currency = detail.ns_currency_id

                    child = {
                        'id': detail.id,
                        'parent_id': bill.id,
                        'name': detail.ns_partner_id.name,
                        'level': 3,
                        'class': 'text',
                        'columns': [
                            {'name': detail.ns_original_sales_order_id.name},
                            {'name': detail.ns_start_date},
                            {'name': detail.ns_subscription_start_date},
                            {'name': detail.ns_subscription_end_date},
                            {'name': detail.ns_operation_site_id.name},
                            {'name': detail.ns_product_code},
                            {'name': detail.ns_product_name},
                            {'name': detail.ns_quantity, 'class': 'number'},
                            {'name': detail.ns_uom_id.name},
                            {'name': self.format_value(detail.ns_price_unit, currency=detail.ns_currency_id), 'class': 'number'},
                            {'name': self.format_value(detail.ns_mrc_price_unit, currency=detail.ns_currency_id), 'class': 'number'},
                            {'name': self.format_value(detail.ns_nrc_price_unit, currency=detail.ns_currency_id), 'class': 'number'},
                            {'name': self.format_value(detail.ns_tax, currency=detail.ns_currency_id), 'class': 'number'},
                            {'name': self.format_value(detail.ns_total, currency=detail.ns_currency_id), 'class': 'number'}
                        ]
                    }

                    if last_order_id != detail.ns_original_sales_order_id.id:
                        last_order_id = detail.ns_original_sales_order_id.id
                        separator_child = {
                            'id': detail.ns_original_sales_order_id,
                            'parent_id': bill.id,
                            'name': detail.ns_original_sales_order_id.name,
                            'level': 2,
                            'class': 'text',
                            'columns': [
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                            ]
                        }

                        childs.append(separator_child)

                    childs.append(child)

            if total_qty > 0:
                item['columns'][7] = {'name': total_qty, 'class': 'number'}
                item['columns'][9] = {'name': self.format_value(total_cost, currency=currency), 'class': 'number'}
                item['columns'][10] = {'name': self.format_value(total_mrc, currency=currency), 'class': 'number'}
                item['columns'][11] = {'name': self.format_value(total_nrc, currency=currency), 'class': 'number'}
                item['columns'][12] = {'name': self.format_value(total_tax, currency=currency), 'class': 'number'}
                item['columns'][13] = {'name': self.format_value(grand_total, currency=currency), 'class': 'number'}

                result.append(item)
                result += childs

        
        return result