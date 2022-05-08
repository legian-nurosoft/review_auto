# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    company_id = fields.Many2one('res.company', string='Company', default=False, required=False)
    ns_related_operation_site_id = fields.Many2one('operating.sites', string='Related Operation Site', oldname='ns_related_operation_site')
    ns_related_de_company_id = fields.Many2one('res.company', string='Related DE Company', oldname='ns_related_de_company')
    ns_related_cost_center_id = fields.Many2one('hr.department', string='Related Cost Center', oldname='ns_related_cost_center')


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        missing_fields = set(['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        account_analytic_id = asset.account_analytic_id
        ns_cost_center_id = asset.ns_cost_center_id
        ns_site_id = asset.ns_site_id
        ns_project_id = asset.ns_project_id
        ns_company_id = asset.ns_company_id
        analytic_tag_ids = asset.analytic_tag_ids
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount_currency = vals['amount']
        amount = current_currency._convert(amount_currency, company_currency, asset.company_id, depreciation_date)
        # Keep the partner on the original invoice if there is only one
        partner = asset.original_move_line_ids.mapped('partner_id')
        partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
        if asset.original_move_line_ids and asset.original_move_line_ids[0].move_id.move_type in ['in_refund', 'out_refund']:
            amount = -amount
            amount_currency = -amount_currency
        move_line_1 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type == 'sale' else False,
            'ns_cost_center_id': ns_cost_center_id.id if asset.asset_type == 'sale' else False,
            'ns_site_id': ns_site_id.id if asset.asset_type == 'sale' else False,
            'ns_project_id': ns_project_id.id if asset.asset_type == 'sale' else False,
            'ns_company_id': ns_company_id.id if asset.asset_type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
            'currency_id': current_currency.id,
            'amount_currency': -amount_currency,
        }
        move_line_2 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'ns_cost_center_id': ns_cost_center_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'ns_site_id': ns_site_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'ns_project_id': ns_project_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'ns_company_id': ns_company_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in ('purchase', 'expense') else False,
            'currency_id': current_currency.id,
            'amount_currency': amount_currency,
        }
        move_vals = {
            'ref': vals['move_ref'],
            'partner_id': partner.id,
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'asset_id': asset.id,
            'asset_remaining_value': vals['asset_remaining_value'],
            'asset_depreciated_value': vals['asset_depreciated_value'],
            'amount_total': amount,
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'move_type': 'entry',
            'currency_id': current_currency.id,
        }
        return move_vals


class AccountMoveLineInherit(models.Model):    
    _inherit = 'account.move.line'

    ns_cost_center_id = fields.Many2one('account.analytic.account', 'Cost Center', domain='[("group_id.name", "=", "Cost Center")]')
    ns_site_id = fields.Many2one('account.analytic.account', 'Site', domain='[("group_id.name", "=", "Site")]')
    ns_project_id = fields.Many2one('account.analytic.account', 'Project', domain='[("group_id.name", "=", "Project")]')
    ns_company_id = fields.Many2one('account.analytic.account', 'Company', domain='[("group_id.name", "=", "Company")]')

    @api.onchange('product_id')
    def _compute_ns_company_site(self):
        company_id = self.company_id
        company_name = company_id.name.lower()
        analytics = self.env['account.analytic.account'].search(
            [('group_id.name', '=', 'Company')])
        for analytic in analytics:
            if analytic.code:
                if analytic.ns_related_de_company_id == company_id or analytic.code.lower() == company_name:
                    self.ns_company_id = analytic.id
        move = self.move_id
        if move.journal_id.type == 'sale':
            if move.ns_operation_site:
                analytics = self.env['account.analytic.account'].search(
                    [('group_id.name', '=', 'Site'), ('name', '=', move.ns_operation_site.name)], limit=1)
                self.ns_site_id = analytics.id

    def create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic account or an analytic distribution.
        """
        super(AccountMoveLineInherit,self).create_analytic_lines()
        lines_to_create_analytic_entries = self.env['account.move.line']
        analytic_line_vals = []
        for obj_line in self:
            if obj_line.ns_cost_center_id or obj_line.ns_site_id or obj_line.ns_project_id or obj_line.ns_company_id:
                lines_to_create_analytic_entries |= obj_line

        # create analytic entries in batch
        if lines_to_create_analytic_entries:
            analytic_line_vals += lines_to_create_analytic_entries._prepare_additional_analytic_line()

        self.env['account.analytic.line'].create(analytic_line_vals)

    def _prepare_additional_analytic_line(self):
        res = []
        for move_line in self:            
            amount = (move_line.credit or 0.0) - (move_line.debit or 0.0)
            default_name = move_line.name or (move_line.ref or '/' + ' -- ' + (move_line.partner_id and move_line.partner_id.name or '/'))
            if move_line.ns_cost_center_id:
                res.append({
                    'name': default_name,
                    'date': move_line.date,
                    'account_id': move_line.ns_cost_center_id.id,
                    'group_id': move_line.analytic_account_id.group_id.id,
                    'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
                    'unit_amount': move_line.quantity,
                    'product_id': move_line.product_id and move_line.product_id.id or False,
                    'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
                    'amount': amount,
                    'general_account_id': move_line.account_id.id,
                    'ref': move_line.ref,
                    'move_id': move_line.id,
                    'user_id': move_line.move_id.invoice_user_id.id or self._uid,
                    'partner_id': move_line.partner_id.id,
                    'company_id': move_line.analytic_account_id.company_id.id or self.env.company.id,
                })

            if move_line.ns_site_id:
                res.append({
                    'name': default_name,
                    'date': move_line.date,
                    'account_id': move_line.ns_site_id.id,
                    'group_id': move_line.analytic_account_id.group_id.id,
                    'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
                    'unit_amount': move_line.quantity,
                    'product_id': move_line.product_id and move_line.product_id.id or False,
                    'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
                    'amount': amount,
                    'general_account_id': move_line.account_id.id,
                    'ref': move_line.ref,
                    'move_id': move_line.id,
                    'user_id': move_line.move_id.invoice_user_id.id or self._uid,
                    'partner_id': move_line.partner_id.id,
                    'company_id': move_line.analytic_account_id.company_id.id or self.env.company.id,
                })

            if move_line.ns_project_id:
                res.append({
                    'name': default_name,
                    'date': move_line.date,
                    'account_id': move_line.ns_project_id.id,
                    'group_id': move_line.analytic_account_id.group_id.id,
                    'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
                    'unit_amount': move_line.quantity,
                    'product_id': move_line.product_id and move_line.product_id.id or False,
                    'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
                    'amount': amount,
                    'general_account_id': move_line.account_id.id,
                    'ref': move_line.ref,
                    'move_id': move_line.id,
                    'user_id': move_line.move_id.invoice_user_id.id or self._uid,
                    'partner_id': move_line.partner_id.id,
                    'company_id': move_line.analytic_account_id.company_id.id or self.env.company.id,
                })

            if move_line.ns_company_id:
                res.append({
                    'name': default_name,
                    'date': move_line.date,
                    'account_id': move_line.ns_company_id.id,
                    'group_id': move_line.analytic_account_id.group_id.id,
                    'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
                    'unit_amount': move_line.quantity,
                    'product_id': move_line.product_id and move_line.product_id.id or False,
                    'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
                    'amount': amount,
                    'general_account_id': move_line.account_id.id,
                    'ref': move_line.ref,
                    'move_id': move_line.id,
                    'user_id': move_line.move_id.invoice_user_id.id or self._uid,
                    'partner_id': move_line.partner_id.id,
                    'company_id': move_line.analytic_account_id.company_id.id or self.env.company.id,
                })
        
        return res
