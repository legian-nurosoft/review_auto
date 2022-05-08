# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        mrc_lines = []
        nrc_lines = []
        new_lines = []
        sequence = 0

        for line in res['invoice_line_ids']:
            product = self.env['product.product'].browse(line[2]['product_id'])
            if product.recurring_invoice:
                mrc_lines.append(line)
            else:
                line[2]['subscription_start_date'] = False
                line[2]['subscription_end_date'] = False
                nrc_lines.append(line)
        
        if len(nrc_lines) != 0:
            new_lines.append(
                {
                    'sequence': sequence,
                    'name': 'Non Recurring Charge (NRC)',
                    'subscription_id': False,
                    'price_unit': False,
                    'discount': False,
                    'quantity': False,
                    'product_uom_id': False,
                    'product_id': False,
                    'tax_ids': False,
                    'analytic_account_id': False,
                    'analytic_tag_ids': False,
                    'subscription_start_date': False,
                    'subscription_end_date': False,
                    'display_type': 'line_section'
                }
            )
            sequence += 1
            
            for line in nrc_lines:
                line[2]['sequence'] = sequence
                new_lines.append(line)
                sequence += 1

        if len(mrc_lines) != 0:
            new_lines.append(
                {	
                    'sequence': sequence,
                    'name': 'Monthly Recurring Charge (MRC)',
                    'subscription_id': False,
                    'price_unit': False,
                    'discount': False,
                    'quantity': False,
                    'product_uom_id': False,
                    'product_id': False,
                    'tax_ids': False,
                    'analytic_account_id': False,
                    'analytic_tag_ids': False,
                    'subscription_start_date': False,
                    'subscription_end_date': False,
                    'display_type': 'line_section'
                }
            )
            sequence += 1

            for line in mrc_lines:
                line[2]['sequence'] = sequence
                new_lines.append(line)
                sequence += 1

        res['invoice_line_ids'] = new_lines
        return res
