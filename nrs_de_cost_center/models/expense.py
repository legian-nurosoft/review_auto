# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class HrExpense(models.Model):    
    _inherit = 'hr.expense'

    ns_cost_center_id = fields.Many2one('account.analytic.account', 'Cost Center', domain='[("group_id.name", "=", "Cost Center")]')
    ns_site_id = fields.Many2one('account.analytic.account', 'Site', domain='[("group_id.name", "=", "Site")]')
    ns_project_id = fields.Many2one('account.analytic.account', 'Project', domain='[("group_id.name", "=", "Project")]')
    ns_company_id = fields.Many2one('account.analytic.account', 'Company', domain='[("group_id.name", "=", "Company")]')
    ns_set_total_manual = fields.Boolean(string="Set Manual")
    ns_total_amount_company_manual = fields.Monetary("Total (Company Currency - Manual)", store=True, currency_field='company_currency_id')

    ns_set_total_manual = fields.Boolean(string="Set Manual", copy=False)
    ns_total_amount_company_manual = fields.Monetary("Total (Company Currency - Manual)", store=True, currency_field='company_currency_id', copy=False)
    ns_total_amount_company_manual_untax = fields.Monetary(store=True, currency_field='company_currency_id', copy=False)
    ns_is_set_tax = fields.Boolean(copy=False)
    ns_is_tax_required = fields.Boolean('Is Tax Required')
    
    def set_tax_for_amount_company_manual(self):
        """set tax for manual currency amount"""
        for rec in self:
            if not rec.ns_is_set_tax:
                total_untax = rec.ns_total_amount_company_manual
                rec.ns_total_amount_company_manual_untax = total_untax
                rec.ns_total_amount_company_manual = rec.tax_ids.with_context(round=True).compute_all(rec.ns_total_amount_company_manual)['total_included']
                rec.ns_is_set_tax=True
                
    def unset_tax_for_amount_company_manual(self):
        """unset tax for manual currency amount"""
        for rec in self:
            if rec.ns_is_set_tax:
                rec.ns_total_amount_company_manual = rec.ns_total_amount_company_manual_untax
                rec.ns_is_set_tax=False

    ns_expense_claim_on_behalf = fields.Boolean(string='Expense Claim on behalf of other employee', default=False)
    ns_other_employee = fields.Many2one('hr.employee', string='Other Employee')
    ns_input_tax = fields.Monetary("Input Tax", store=True, currency_field='company_currency_id',
                                   compute='_compute_expense_tax')

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_expense_tax(self):
        for expense in self:
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity,
                                                expense.product_id, expense.employee_id.user_id.partner_id)
            expense.ns_input_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

    @api.onchange('ns_other_employee')
    def update_employee_id(self):
        if self.ns_other_employee:
            self.employee_id = self.ns_other_employee.id

    @api.onchange('company_id')
    def update_ns_company_id(self):
        company_id = self.company_id
        company_name = company_id.name.lower()
        analytics = self.env['account.analytic.account'].search(
            [('group_id.name', '=', 'Company')])
        for analytic in analytics:
            if analytic.ns_related_de_company_id == company_id or analytic.code.lower() == company_name:
                self.ns_company_id = analytic.id

    @api.depends('date', 'total_amount', 'company_currency_id', 'ns_total_amount_company_manual', 'ns_set_total_manual')
    def _compute_total_amount_company(self):
        """set total amount company manual if boolean set"""
        res = super(HrExpense, self)._compute_total_amount_company()
        for expense in self:
            if expense.ns_set_total_manual:
                expense.total_amount_company = expense.ns_total_amount_company_manual
        return res
        
    @api.onchange('employee_id')
    def update_cost_center_id(self):
        self.ns_cost_center_id = self.employee_id.ns_cost_center_id

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.sudo().address_home_id.commercial_partner_id.id

            # source move line
            balance = expense.currency_id._convert(taxes['total_excluded'], company_currency, expense.company_id, account_date)
            amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': balance if balance > 0 else 0,
                'credit': -balance if balance < 0 else 0,
                'amount_currency': amount_currency,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,                
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'ns_cost_center_id': expense.ns_cost_center_id.id,
                'ns_site_id': expense.ns_site_id.id,
                'ns_project_id': expense.ns_project_id.id,
                'ns_company_id': expense.ns_company_id.id,
                'expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'tax_tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': expense.currency_id.id,
            }
            move_line_values.append(move_line_src)
            total_amount -= balance
            total_amount_currency -= move_line_src['amount_currency']

            # taxes move lines
            for tax in taxes['taxes']:
                balance = expense.currency_id._convert(tax['amount'], company_currency, expense.company_id, account_date)
                amount_currency = tax['amount']

                if tax['tax_repartition_line_id']:
                    rep_ln = self.env['account.tax.repartition.line'].browse(tax['tax_repartition_line_id'])
                    base_amount = self.env['account.move']._get_base_amount_to_display(tax['base'], rep_ln)
                    base_amount = expense.currency_id._convert(base_amount, company_currency, expense.company_id, account_date)
                else:
                    base_amount = None

                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': balance if balance > 0 else 0,
                    'credit': -balance if balance < 0 else 0,
                    'amount_currency': amount_currency,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tax_tag_ids': tax['tag_ids'],
                    'tax_base_amount': base_amount,
                    'expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                    'ns_cost_center_id': expense.ns_cost_center_id.id if tax['analytic'] else False,
                    'ns_site_id': expense.ns_site_id.id if tax['analytic'] else False,
                    'ns_project_id': expense.ns_project_id.id if tax['analytic'] else False,
                    'ns_company_id': expense.ns_company_id.id if tax['analytic'] else False,
                }
                total_amount -= balance
                total_amount_currency -= move_line_tax_values['amount_currency']
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency,
                'currency_id': expense.currency_id.id,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    @api.onchange('company_id')
    def update_is_tax_required(self):
        self.ns_is_tax_required = self.company_id.ns_expense_required_tax

class HrExpensesSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    x_studio_i_accept_user_electronic_agreementdeclaration = fields.Boolean('I accept \'User Electronic Agreement/Declaration\'')

    def action_submit_sheet(self):
        if self.x_studio_i_accept_user_electronic_agreementdeclaration:
            super(HrExpensesSheet, self).action_submit_sheet()
        else:
            raise UserError(_("Please check the User Electronic Agreement/Declaration before submitting the expense report."))
