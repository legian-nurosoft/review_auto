# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields


class report_account_consolidated_journal(models.AbstractModel):
    _inherit = "account.consolidated.journal"


    def _get_columns_name(self, options):
        columns = [{'name': _('Journal Name (Code)')}, {'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}, {'name': _('Balance'), 'class': 'number'}]
        
        if options.get('show_usd_real',False):
            columns.insert(1,{'name': 'Balance USD Real'})
            columns.insert(1,{'name': 'Credit USD Real'})
            columns.insert(1,{'name': 'Debit USD Real'})

        if options.get('show_usd_budget',False):
            columns.insert(1,{'name': 'Balance USD Budget'})
            columns.insert(1,{'name': 'Credit USD Budget'})
            columns.insert(1,{'name': 'Debit USD Budget'})

        return columns    

    def _get_journal_line(self, options, current_journal, results, record):
        return {
                'id': 'journal_%s' % current_journal,
                'name': '%s (%s)' % (record['journal_name'], record['journal_code']),
                'level': 2,
                'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['journal_id'] == current_journal, options=options)],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('journal_%s' % (current_journal,), options),
            }

    def _get_account_line(self, options, current_journal, current_account, results, record):
        return {
                'id': 'account_%s_%s' % (current_account,current_journal),
                'name': '%s %s' % (record['account_code'], record['account_name']),
                'level': 3,
                'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['account_id'] == current_account and x['journal_id'] == current_journal, options=options)],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('account_%s_%s' % (current_account, current_journal), options),
                'parent_id': 'journal_%s' % (current_journal),
            }

    def _get_line_total_per_month(self, options, current_company, results):
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        lines = []
        lines.append({
                    'id': 'Total_all_%s' % (current_company),
                    'name': _('Total'),
                    'class': 'total',
                    'level': 1,
                    'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['company_id'] == current_company, options=options)]
        })

        blank_line_after_total = {
            'id': 'blank_line_after_total_%s' % (current_company),
            'name': '',
            'columns': [{'name': ''} for n in ['debit', 'credit', 'balance']]
        }

        if options.get('show_usd_real',False):
            blank_line_after_total['columns'] += [{'name': ''} for n in ['debit', 'credit', 'balance']]

        if options.get('show_usd_budget',False):
            blank_line_after_total['columns'] += [{'name': ''} for n in ['debit', 'credit', 'balance']]

        lines.append(blank_line_after_total)
        # get range of date for company_id
        dates = []
        for record in results:
            date = '%s-%s' % (record['yyyy'], record['month'])
            if date not in dates:
                dates.append(date)
        if dates:
            detail_per_month = {'id': 'Detail_%s' % (current_company),
                'name': _('Details per month'),
                'level': 1,
                'columns': [{},{},{}]
            }
            if options.get('show_usd_real',False):
                detail_per_month['columns'] += [{},{},{}]

            if options.get('show_usd_budget',False):
                detail_per_month['columns'] += [{},{},{}]

            lines.append(detail_per_month)

            for date in sorted(dates):
                year, month = date.split('-')
                sum_debit = self.format_value(sum([r['debit'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_credit = self.format_value(sum([r['credit'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_balance = self.format_value(sum([r['balance'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                vals = {
                        'id': 'Total_month_%s_%s' % (date, current_company),
                        'name': convert_date('%s-01' % (date), {'format': 'MMM yyyy'}),
                        'level': 2,
                        'columns': [{'name': v} for v in [sum_debit, sum_credit, sum_balance]]
                }

                if options.get('show_usd_real',False):
                    sum_debit_real = self.format_value(sum([r['debit_real'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    sum_credit_real = self.format_value(sum([r['credit_real'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    sum_balance_real = self.format_value(sum([r['balance_real'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    
                    vals['columns'].insert(0, {'name': sum_balance_real})
                    vals['columns'].insert(0, {'name': sum_credit_real})
                    vals['columns'].insert(0, {'name': sum_debit_real})
                    
                if options.get('show_usd_budget',False):
                    sum_debit_budget = self.format_value(sum([r['debit_budget'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    sum_credit_budget = self.format_value(sum([r['credit_budget'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    sum_balance_budget = self.format_value(sum([r['balance_budget'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]), currency=usd_currency)
                    
                    vals['columns'].insert(0, {'name': sum_balance_budget})
                    vals['columns'].insert(0, {'name': sum_credit_budget})
                    vals['columns'].insert(0, {'name': sum_debit_budget})

                lines.append(vals)
        return lines

    def _get_sum(self, results, lambda_filter, options={}):
        sum_debit = self.format_value(sum([r['debit'] for r in results if lambda_filter(r)]))
        sum_credit = self.format_value(sum([r['credit'] for r in results if lambda_filter(r)]))
        sum_balance = self.format_value(sum([r['balance'] for r in results if lambda_filter(r)]))
        
        columns = [sum_debit, sum_credit, sum_balance]

        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)

        if options.get('show_usd_real',False):
            sum_debit_real = self.format_value(sum([r['debit_real'] for r in results if lambda_filter(r)]), currency=usd_currency)
            sum_credit_real = self.format_value(sum([r['credit_real'] for r in results if lambda_filter(r)]), currency=usd_currency)
            sum_balance_real = self.format_value(sum([r['balance_real'] for r in results if lambda_filter(r)]), currency=usd_currency)

            columns.insert(0,sum_balance_real)
            columns.insert(0,sum_credit_real)
            columns.insert(0,sum_debit_real)

        if options.get('show_usd_budget',False):
            sum_debit_budget = self.format_value(sum([r['debit_budget'] for r in results if lambda_filter(r)]), currency=usd_currency)
            sum_credit_budget = self.format_value(sum([r['credit_budget'] for r in results if lambda_filter(r)]), currency=usd_currency)
            sum_balance_budget = self.format_value(sum([r['balance_budget'] for r in results if lambda_filter(r)]), currency=usd_currency)

            columns.insert(0,sum_balance_budget)
            columns.insert(0,sum_credit_budget)
            columns.insert(0,sum_debit_budget)

        return columns


    @api.model
    def _get_lines(self, options, line_id=None):
        # 1.Build SQL query
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        lines = []
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        select = """
            SELECT to_char("account_move_line".date, 'MM') as month,
                   to_char("account_move_line".date, 'YYYY') as yyyy,
                   COALESCE(SUM("account_move_line".balance), 0) as balance,
                   COALESCE(SUM("account_move_line".debit), 0) as debit,
                   COALESCE(SUM("account_move_line".credit), 0) as credit,
                   COALESCE(SUM("account_move_line".ns_debit_usd_budget - "account_move_line".ns_credit_usd_budget), 0) as balance_budget,
                   COALESCE(SUM("account_move_line".ns_debit_usd_budget), 0) as debit_budget,
                   COALESCE(SUM("account_move_line".ns_credit_usd_budget), 0) as credit_budget,
                   COALESCE(SUM("account_move_line".ns_debit_usd_real - "account_move_line".ns_credit_usd_real), 0) as balance_real,
                   COALESCE(SUM("account_move_line".ns_debit_usd_real), 0) as debit_real,
                   COALESCE(SUM("account_move_line".ns_credit_usd_real), 0) as credit_real,
                   j.id as journal_id,
                   j.name as journal_name, j.code as journal_code,
                   account.name as account_name, account.code as account_code,
                   j.company_id, account_id
            FROM %s, account_journal j, account_account account, res_company c
            WHERE %s
              AND "account_move_line".journal_id = j.id
              AND "account_move_line".account_id = account.id
              AND j.company_id = c.id
            GROUP BY month, account_id, yyyy, j.id, account.id, j.company_id
            ORDER BY j.id, account_code, yyyy, month, j.company_id
        """
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        line_model = None
        if line_id:
            split_line_id = line_id.split('_')
            line_model = split_line_id[0]
            model_id = split_line_id[1]
            where_clause += line_model == 'account' and ' AND account_id = %s AND j.id = %s' or  ' AND j.id = %s'
            where_params += [str(model_id)]
            if line_model == 'account':
                where_params +=[str(split_line_id[2])] # We append the id of the parent journal in case of an account line

        if options.get('show_ifrs', False) or options.get('show_gaap', False):
            ifrs_gaap_clause = ''
            
            if options.get('show_ifrs', False):
                ifrs_gaap_clause += "'IFRS',"
            
            if options.get('show_gaap', False):
                ifrs_gaap_clause += "'GAAP',"

            ifrs_gaap_clause = " AND ( account_move_line.ns_fr IS NULL OR account_move_line.ns_fr IN (" + ifrs_gaap_clause[:-1] + ")) "
            where_clause += ifrs_gaap_clause
        
        # 2.Fetch data from DB
        select = select % (tables, where_clause)
        
        self.env.cr.execute(select, where_params)
        results = self.env.cr.dictfetchall()
        if not results:
            return lines

        # 3.Build report lines
        current_account = None
        current_journal = line_model == 'account' and results[0]['journal_id'] or None # If line_id points toward an account line, we don't want to regenerate the parent journal line
        for values in results:
            if values['journal_id'] != current_journal:
                current_journal = values['journal_id']
                lines.append(self._get_journal_line(options, current_journal, results, values))

            if self._need_to_unfold('journal_%s' % (current_journal,), options) and values['account_id'] != current_account:
                current_account = values['account_id']
                lines.append(self._get_account_line(options, current_journal, current_account, results, values))

            # If we need to unfold the line
            if self._need_to_unfold('account_%s_%s' % (values['account_id'], values['journal_id']), options):
                vals = {
                    'id': 'month_%s__%s_%s_%s' % (values['journal_id'], values['account_id'], values['month'], values['yyyy']),
                    'name': convert_date('%s-%s-01' % (values['yyyy'], values['month']), {'format': 'MMM yyyy'}),
                    'caret_options': True,
                    'level': 4,
                    'parent_id': "account_%s_%s" % (values['account_id'], values['journal_id']),
                    'columns': [{'name': n} for n in [self.format_value(values['debit']), self.format_value(values['credit']), self.format_value(values['balance'])]],
                }

                if options.get('show_usd_real',False):
                    vals['columns'].insert(0, {'name': self.format_value(values['balance_real'], currency=usd_currency)})
                    vals['columns'].insert(0, {'name': self.format_value(values['credit_real'], currency=usd_currency)})
                    vals['columns'].insert(0, {'name': self.format_value(values['debit_real'], currency=usd_currency)})

                if options.get('show_usd_budget',False):
                    vals['columns'].insert(0, {'name': self.format_value(values['balance_budget'], currency=usd_currency)})
                    vals['columns'].insert(0, {'name': self.format_value(values['credit_budget'], currency=usd_currency)})
                    vals['columns'].insert(0, {'name': self.format_value(values['debit_budget'], currency=usd_currency)})
                
                lines.append(vals)

        # Append detail per month section
        if not line_id:
            lines.extend(self._get_line_total_per_month(options, values['company_id'], results))
        return lines