# -*- coding: utf-8 -*-

from copy import deepcopy
from odoo import models, api, _, fields
from pprint import pprint

class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = "account.coa.report"


    @api.model
    def _get_columns(self, options):
        header1 = [
            {'name': '', 'style': 'width:40%'},            
        ]

        header_1_initial = [
            {'name': _('Initial Balance'), 'class': 'number', 'colspan': 2},
        ]

        if options.get('show_usd_real',False):
            header_1_initial[0]['colspan'] += 2

        if options.get('show_usd_budget',False):
            header_1_initial[0]['colspan'] += 2 

        header1 += header_1_initial        

        for period in reversed(options['comparison'].get('periods', [])):
            header1_comparison = [
                {'name': period['string'], 'class': 'number', 'colspan': 2}
            ]

            if options.get('show_usd_real',False):
                header1_comparison[0]['colspan'] += 2

            if options.get('show_usd_budget',False):
                header1_comparison[0]['colspan'] += 2

            header1 += header1_comparison

        header1_current_periode = [
            {'name': options['date']['string'], 'class': 'number', 'colspan': 2},            
        ]

        if options.get('show_usd_real',False):
            header1_current_periode[0]['colspan'] += 2

        if options.get('show_usd_budget',False):
            header1_current_periode[0]['colspan'] += 2

        header1 += header1_current_periode

        header_1_total = [
            {'name': _('Total'), 'class': 'number', 'colspan': 3},
        ]

        if options.get('show_usd_real',False):
            header_1_total[0]['colspan'] += 2

        if options.get('show_usd_budget',False):
            header_1_total[0]['colspan'] += 2

        header1 += header_1_total

        header2 = [
            {'name': '', 'style': 'width:40%'},            
        ]

        if options.get('show_usd_budget',False):
            header2 += [
                {'name': _('Debit USD Budget'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Budget'), 'class': 'number o_account_coa_column_contrast'}
            ]

        if options.get('show_usd_real',False):
            header2 += [
                {'name': _('Debit USD Real'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Real'), 'class': 'number o_account_coa_column_contrast'}
            ]

        header2_initial = [
            {'name': _('Debit'), 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'class': 'number o_account_coa_column_contrast'},
        ]

        header2 += header2_initial

        if options.get('comparison') and options['comparison'].get('periods'):
            header2_comparison = []
            if options.get('show_usd_budget',False):
                header2_comparison += [
                    {'name': _('Debit USD Budget'), 'class': 'number o_account_coa_column_contrast'},
                    {'name': _('Credit USD Budget'), 'class': 'number o_account_coa_column_contrast'}
                ]

            if options.get('show_usd_real',False):
                header2_comparison += [
                    {'name': _('Debit USD Real'), 'class': 'number o_account_coa_column_contrast'},
                    {'name': _('Credit USD Real'), 'class': 'number o_account_coa_column_contrast'}
                ]

            header2_comparison += [
                {'name': _('Debit'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit'), 'class': 'number o_account_coa_column_contrast'},
            ]


            header2 +=  header2_comparison * len(options['comparison']['periods'])

        if options.get('show_usd_budget',False):
            header2 += [
                {'name': _('Debit USD Budget'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Budget'), 'class': 'number o_account_coa_column_contrast'}
            ]

        if options.get('show_usd_real',False):
            header2 += [
                {'name': _('Debit USD Real'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Real'), 'class': 'number o_account_coa_column_contrast'}
            ]
        
        header2 += [
            {'name': _('Debit'), 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'class': 'number o_account_coa_column_contrast'},            
        ]

        if options.get('show_usd_budget',False):
            header2 += [
                {'name': _('Debit USD Budget'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Budget'), 'class': 'number o_account_coa_column_contrast'}
            ]

        if options.get('show_usd_real',False):
            header2 += [
                {'name': _('Debit USD Real'), 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit USD Real'), 'class': 'number o_account_coa_column_contrast'}
            ]

        header2 += [
            {'name': _('Debit'), 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Balance'), 'class': 'number o_account_coa_column_contrast'},
        ]
        
        if options['comparison']['filter'] != 'no_comparison' and options['comparison']['number_period'] == 1:
            header1+=[
                {'name': _('%'), 'class': 'number', 'colspan': 1},
            ]
            header2+=[
                {'name': _('Variance'), 'class': 'number', 'colspan': 1},
            ]
        return [header1, header2]


    @api.model
    def _get_lines(self, options, line_id=None):
        # Create new options with 'unfold_all' to compute the initial balances.
        # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        usd_index = []
        new_options = options.copy()
        new_options['unfold_all'] = True
        options_list = self._get_options_periods_list(new_options)
        accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=False)

        lines = []
        totals = [0.0] * (2 * (len(options_list) + 2)) + [0.0]
        
        option_multiply = len(options_list) -1 if len(options_list) > 1 else len(options_list)
        if options.get('show_usd_budget',False):
            totals += [0.0] * (2 * (len(options_list) + 2))

        if options.get('show_usd_real',False):
            totals += [0.0] * (2 * (len(options_list) + 2))

        
        # Add lines, one per account.account record.
        for account, periods_results in accounts_results:
            sums = []
            account_balance = 0.0
            budget_balance = real_balance = 0.0

            for i, period_values in enumerate(reversed(periods_results)):
                account_sum = period_values.get('sum', {})
                account_un_earn = period_values.get('unaffected_earnings', {})
                account_init_bal = period_values.get('initial_balance', {})

                if i == 0:
                    # Append the initial balances.
                    initial_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                    initial_balance_budget = (account_init_bal.get('debit_budget', 0.0) - account_init_bal.get('credit_budget', 0.0)) + (account_un_earn.get('debit_budget', 0.0) - account_un_earn.get('credit_budget', 0.0))
                    initial_balance_real = (account_init_bal.get('debit_real', 0.0) - account_init_bal.get('credit_real', 0.0)) + (account_un_earn.get('debit_real', 0.0) - account_un_earn.get('credit_real', 0.0))
                    
                    if options.get('show_usd_budget',False):
                        sums += [
                            [initial_balance_budget > 0 and initial_balance_budget or 0.0],
                            [initial_balance_budget < 0 and -initial_balance_budget or 0.0],
                        ]

                    if options.get('show_usd_real',False):
                        sums += [
                            [initial_balance_real > 0 and initial_balance_real or 0.0],
                            [initial_balance_real < 0 and -initial_balance_real or 0.0],
                        ]

                    sums += [
                        initial_balance > 0 and initial_balance or 0.0,
                        initial_balance < 0 and -initial_balance or 0.0,
                    ]
                    account_balance += initial_balance
                    budget_balance += initial_balance_budget
                    real_balance += initial_balance_real

                # Append the debit/credit columns.

                if options.get('show_usd_budget',False):
                    sums += [
                        [account_sum.get('debit_budget', 0.0) - account_init_bal.get('debit_budget', 0.0)],
                        [account_sum.get('credit_budget', 0.0) - account_init_bal.get('credit_budget', 0.0)],
                    ]
                    budget_balance += sums[-2][0] - sums[-1][0]

                if options.get('show_usd_real',False):
                    sums += [
                        [account_sum.get('debit_real', 0.0) - account_init_bal.get('debit_real', 0.0)],
                        [account_sum.get('credit_real', 0.0) - account_init_bal.get('credit_real', 0.0)],
                    ]
                    real_balance += sums[-2][0] - sums[-1][0]

                sums += [
                    account_sum.get('debit', 0.0) - account_init_bal.get('debit', 0.0),
                    account_sum.get('credit', 0.0) - account_init_bal.get('credit', 0.0),
                ]
                account_balance += sums[-2] - sums[-1]              

                

            if options.get('show_usd_budget',False):
                sums += [
                    [budget_balance > 0 and budget_balance or 0.0],
                    [budget_balance < 0 and -budget_balance or 0.0],
                ]

            if options.get('show_usd_real',False):
                sums += [
                    [real_balance > 0 and real_balance or 0.0],
                    [real_balance < 0 and -real_balance or 0.0],
                ]

                
            # Append the totals.
            sums += [
                account_balance > 0 and account_balance or 0.0,
                account_balance < 0 and -account_balance or 0.0,
            ]
            
            sums += [
                account_balance      
            ]

            # account.account report line.
            columns = []
            for i, value in enumerate(sums):
                # Update totals.
                if isinstance(value, list):
                    if i not in usd_index:
                        usd_index.append(i)

                    totals[i] += value[0]
                    # Create columns.
                    columns.append({'name': self.format_value(value[0], currency=usd_currency, blank_if_zero=True), 'class': 'number', 'no_format_name': value[0]})
                else:
                    totals[i] += value
                    # Create columns.
                    columns.append({'name': self.format_value(value, blank_if_zero=True), 'class': 'number', 'no_format_name': value})

            name = account.name_get()[0][1]
            
            # Calculate percent variance 
            if options['comparison']['filter'] != 'no_comparison' and options['comparison']['number_period'] == 1:
                value_percentage = 0
                column_previous_debit = 0
                column_previous_credit = 0
                column_current_debit = 0
                column_current_credit = 0
                if options.get('show_usd_real',False) and options.get('show_usd_budget',False):
                    column_previous_debit = columns[10]['no_format_name']
                    column_previous_credit = columns[11]['no_format_name']
                    column_current_debit = columns[16]['no_format_name']
                    column_current_credit = columns[17]['no_format_name']
                elif options.get('show_usd_real',False):
                    column_previous_debit =  columns[6]['no_format_name']
                    column_previous_credit = columns[7]['no_format_name']
                    column_current_debit = columns[10]['no_format_name']
                    column_current_credit = columns[11]['no_format_name']
                elif options.get('show_usd_budget',False):
                    column_previous_debit = columns[6]['no_format_name']
                    column_previous_credit = columns[7]['no_format_name']
                    column_current_debit = columns[10]['no_format_name']
                    column_current_credit = columns[11]['no_format_name']
                elif not options.get('show_usd_real',False) and not options.get('show_usd_budget',False):
                    column_previous_debit = columns[2]['no_format_name']
                    column_previous_credit = columns[3]['no_format_name']
                    column_current_debit = columns[4]['no_format_name']
                    column_current_credit = columns[5]['no_format_name']
                    
                if column_previous_debit-column_previous_credit == 0:
                    value_percentage = 'n/a'
                else:
                    value_percentage = round(((column_current_debit-column_current_credit)-(column_previous_debit-column_previous_credit))/(column_previous_debit-column_previous_credit) * 100)
                if value_percentage != 'n/a':
                    if value_percentage < 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number color-red'})
                    elif value_percentage > 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number color-green'})
                    elif value_percentage == 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number'})
                else:
                     columns.append({'name': (str(value_percentage)), 'no_format_name': _(value_percentage), 'class': 'number'})
            
            unfolded = True if options.get('unfold_all') else False
            lines.append({
                'id': account.id,
                'name': name,
                'level': 1,
                'columns': columns,
                'unfoldable': True,
                'unfolded': unfolded,
            })
            
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='analytic_account_id')
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='ns_cost_center_id')
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='ns_site_id')
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='ns_project_id')
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='ns_company_id')
            lines = self._get_lines_analytic(options, line_id=line_id, lines=lines, account_id=account, type='undefined')

        # Total report line.
        total_columns = []
        for i, value in enumerate(totals):
            if i in usd_index:
                total_columns.append({'name': self.format_value(value, currency=usd_currency), 'class': 'number'})
            else:
                total_columns.append({'name': self.format_value(value), 'class': 'number'})

                
        lines.append({
             'id': 'grouped_accounts_total',
             'name': _('Total'),
             'class': 'total o_account_coa_column_contrast',
             'columns': total_columns,
             'level': 1,
        })

        return lines


    @api.model
    def _get_lines_analytic(self, options, line_id=None, lines=[], account_id=0, type='analytic_account_id'):
        # Create new options with 'unfold_all' to compute the initial balances.
        # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        usd_index = []
        new_options = options.copy()
        new_options['unfold_all'] = True
        options_list = self._get_options_periods_list(new_options)
        accounts_results, taxes_results = self._do_query_analytic(options_list, fetch_lines=False, account_id=account_id, type=type)    
        
        option_multiply = len(options_list) -1 if len(options_list) > 1 else len(options_list)       
        
        
        # Add lines, one per account.account record.
        for account, periods_results in accounts_results:
            sums = []
            account_balance = 0.0
            budget_balance = real_balance = 0.0

            for i, period_values in enumerate(reversed(periods_results)):
                account_sum = period_values.get('sum', {})
                account_un_earn = period_values.get('unaffected_earnings', {})
                account_init_bal = period_values.get('initial_balance', {})

                if i == 0:
                    # Append the initial balances.
                    initial_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                    initial_balance_budget = (account_init_bal.get('debit_budget', 0.0) - account_init_bal.get('credit_budget', 0.0)) + (account_un_earn.get('debit_budget', 0.0) - account_un_earn.get('credit_budget', 0.0))
                    initial_balance_real = (account_init_bal.get('debit_real', 0.0) - account_init_bal.get('credit_real', 0.0)) + (account_un_earn.get('debit_real', 0.0) - account_un_earn.get('credit_real', 0.0))
                    
                    if options.get('show_usd_budget',False):
                        sums += [
                            [initial_balance_budget > 0 and initial_balance_budget or 0.0],
                            [initial_balance_budget < 0 and -initial_balance_budget or 0.0],
                        ]

                    if options.get('show_usd_real',False):
                        sums += [
                            [initial_balance_real > 0 and initial_balance_real or 0.0],
                            [initial_balance_real < 0 and -initial_balance_real or 0.0],
                        ]

                    sums += [
                        initial_balance > 0 and initial_balance or 0.0,
                        initial_balance < 0 and -initial_balance or 0.0,
                    ]
                    account_balance += initial_balance
                    budget_balance += initial_balance_budget
                    real_balance += initial_balance_real

                # Append the debit/credit columns.

                if options.get('show_usd_budget',False):
                    sums += [
                        [account_sum.get('debit_budget', 0.0) - account_init_bal.get('debit_budget', 0.0)],
                        [account_sum.get('credit_budget', 0.0) - account_init_bal.get('credit_budget', 0.0)],
                    ]
                    budget_balance += sums[-2][0] - sums[-1][0]

                if options.get('show_usd_real',False):
                    sums += [
                        [account_sum.get('debit_real', 0.0) - account_init_bal.get('debit_real', 0.0)],
                        [account_sum.get('credit_real', 0.0) - account_init_bal.get('credit_real', 0.0)],
                    ]
                    real_balance += sums[-2][0] - sums[-1][0]

                sums += [
                    account_sum.get('debit', 0.0) - account_init_bal.get('debit', 0.0),
                    account_sum.get('credit', 0.0) - account_init_bal.get('credit', 0.0),
                ]
                account_balance += sums[-2] - sums[-1]              

                

            if options.get('show_usd_budget',False):
                sums += [
                    [budget_balance > 0 and budget_balance or 0.0],
                    [budget_balance < 0 and -budget_balance or 0.0],
                ]

            if options.get('show_usd_real',False):
                sums += [
                    [real_balance > 0 and real_balance or 0.0],
                    [real_balance < 0 and -real_balance or 0.0],
                ]

                
            # Append the totals.
            sums += [
                account_balance > 0 and account_balance or 0.0,
                account_balance < 0 and -account_balance or 0.0,
            ]
            
            sums += [
                account_balance      
            ]

            # account.account report line.
            columns = []
            for i, value in enumerate(sums):
                # Update totals.
                if isinstance(value, list):
                    if i not in usd_index:
                        usd_index.append(i)
                    
                    # Create columns.
                    columns.append({'name': self.format_value(value[0], currency=usd_currency, blank_if_zero=True), 'class': 'number', 'no_format_name': value[0]})
                else:
                    # Create columns.
                    columns.append({'name': self.format_value(value, blank_if_zero=True), 'class': 'number', 'no_format_name': value})
            if options['comparison']['filter'] != 'no_comparison' and options['comparison']['number_period'] == 1:
                value_percentage = 0
                column_previous_debit = 0
                column_previous_credit = 0
                column_current_debit = 0
                column_current_credit = 0
                if options.get('show_usd_real',False) and options.get('show_usd_budget',False):
                    column_previous_debit = columns[10]['no_format_name']
                    column_previous_credit = columns[11]['no_format_name']
                    column_current_debit = columns[16]['no_format_name']
                    column_current_credit = columns[17]['no_format_name']
                elif options.get('show_usd_real',False):
                    column_previous_debit =  columns[6]['no_format_name']
                    column_previous_credit = columns[7]['no_format_name']
                    column_current_debit = columns[10]['no_format_name']
                    column_current_credit = columns[11]['no_format_name']
                elif options.get('show_usd_budget',False):
                    column_previous_debit = columns[6]['no_format_name']
                    column_previous_credit = columns[7]['no_format_name']
                    column_current_debit = columns[10]['no_format_name']
                    column_current_credit = columns[11]['no_format_name']
                elif not options.get('show_usd_real',False) and not options.get('show_usd_budget',False):
                    column_previous_debit = columns[2]['no_format_name']
                    column_previous_credit = columns[3]['no_format_name']
                    column_current_debit = columns[4]['no_format_name']
                    column_current_credit = columns[5]['no_format_name']
                if column_previous_debit-column_previous_credit == 0:
                    value_percentage = 'n/a'
                else:
                    value_percentage = round(((column_current_debit-column_current_credit)-(column_previous_debit-column_previous_credit))/(column_previous_debit-column_previous_credit) * 100)
                if value_percentage != 'n/a':
                    if value_percentage < 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number color-red'})
                    elif value_percentage > 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number color-green'})
                    elif value_percentage == 0:
                        columns.append({'name': (str(value_percentage) + '%'), 'no_format_name': _(value_percentage), 'class': 'number'})
                else:
                     columns.append({'name': (str(value_percentage)), 'no_format_name': _(value_percentage), 'class': 'number'})
            name = 'Undefined'
            if account.id:
                name = account.name_get()[0][1]

            lines.append({
                'id': account.id,
                'name': name,
                'title_hover': name,
                'columns': columns,
                'unfoldable': False,
                'ns_analytic_account_id': 1,
                'parent_id': account_id.id,
                'level': 4, 
            })

        return lines


    @api.model
    def _get_query_sums_analytic(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.analytic_account_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND account_move_line.analytic_account_id IS NOT NULL
                GROUP BY account_move_line.analytic_account_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.analytic_account_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND account_move_line.analytic_account_id IS NOT NULL
                    GROUP BY account_move_line.analytic_account_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params

    @api.model
    def _get_query_sums_cost_center(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.ns_cost_center_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND account_move_line.ns_cost_center_id IS NOT NULL
                GROUP BY account_move_line.ns_cost_center_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.ns_cost_center_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND account_move_line.ns_cost_center_id IS NOT NULL
                    GROUP BY account_move_line.ns_cost_center_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params

    @api.model
    def _get_query_sums_site(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.ns_site_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND account_move_line.ns_site_id IS NOT NULL
                GROUP BY account_move_line.ns_site_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.ns_site_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND account_move_line.ns_site_id IS NOT NULL
                    GROUP BY account_move_line.ns_site_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params

    @api.model
    def _get_query_sums_project(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.ns_project_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND account_move_line.ns_project_id IS NOT NULL
                GROUP BY account_move_line.ns_project_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.ns_project_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND account_move_line.ns_project_id IS NOT NULL
                    GROUP BY account_move_line.ns_project_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params

    @api.model
    def _get_query_sums_company(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.ns_company_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND account_move_line.ns_company_id IS NOT NULL
                GROUP BY account_move_line.ns_company_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.ns_company_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND account_move_line.ns_company_id IS NOT NULL
                    GROUP BY account_move_line.ns_company_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params

    @api.model
    def _get_query_sums_undefined(self, options_list, expanded_account=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        options = options_list[0]
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [('account_id', '=', expanded_account.id)] if expanded_account else []

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            queries.append('''
                SELECT
                    account_move_line.analytic_account_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                    SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                    SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                    SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                    SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                    SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                WHERE %s AND 
                account_move_line.analytic_account_id IS NULL AND
                account_move_line.ns_cost_center_id IS NULL AND
                account_move_line.ns_site_id IS NULL AND
                account_move_line.ns_project_id IS NULL AND
                account_move_line.ns_company_id IS NULL
                GROUP BY account_move_line.analytic_account_id
            ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [('account_id.user_type_id.include_initial_balance', '=', False)]
        if expanded_account:
            domain.append(('company_id', '=', expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                %s                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.company_id
        ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = None
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        if domain is not None:
            for i, options_period in enumerate(options_list):

                # The period domain is expressed as:
                # [
                #   ('date' <= options['date_from'] - 1),
                #   '|',
                #   ('date' >= fiscalyear['date_from']),
                #   ('account_id.user_type_id.include_initial_balance', '=', True)
                # ]

                new_options = self._get_options_initial_balance(options_period)
                tables, where_clause, where_params = self._query_get(new_options, domain=domain)
                params += where_params
                queries.append('''
                    SELECT
                        account_move_line.analytic_account_id                            AS groupby,
                        'initial_balance'                                       AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS period_number,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(account_move_line.ns_debit_usd_budget)   AS debit_budget,
                        SUM(account_move_line.ns_credit_usd_budget)   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        SUM(account_move_line.ns_debit_usd_real)   AS debit_real,
                        SUM(account_move_line.ns_credit_usd_real)   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s AND 
                    account_move_line.analytic_account_id IS NULL AND
                    account_move_line.ns_cost_center_id IS NULL AND
                    account_move_line.ns_site_id IS NULL AND
                    account_move_line.ns_project_id IS NULL AND
                    account_move_line.ns_company_id IS NULL
                    GROUP BY account_move_line.analytic_account_id
                ''' % (i, tables, ct_query, where_clause))

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                queries += ['''
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM account_move_line_account_tax_rel tax_rel, %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND %s
                    GROUP BY tax_rel.account_tax_id
                ''' % (i, tables, ct_query, where_clause), '''
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        %s                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        0.0   AS debit_budget,
                        0.0   AS credit_budget,
                        SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)   AS balance_budget,
                        0.0   AS debit_real,
                        0.0   AS credit_real,
                        SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)   AS balance_real
                    FROM %s
                    LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                    WHERE %s
                    GROUP BY account_move_line.tax_line_id
                ''' % (i, tables, ct_query, where_clause)]

        return ' UNION ALL '.join(queries), params


    @api.model
    def _do_query_analytic(self, options_list, expanded_account=None, fetch_lines=True, account_id=0, type='analytic_account_id'):    
        query = params = False
        if type == 'analytic_account_id':
            query, params = self._get_query_sums_analytic(options_list, expanded_account=account_id)
        elif type == 'ns_cost_center_id':
            query, params = self._get_query_sums_cost_center(options_list, expanded_account=account_id)
        elif type == 'ns_site_id':
            query, params = self._get_query_sums_site(options_list, expanded_account=account_id)
        elif type == 'ns_project_id':
            query, params = self._get_query_sums_project(options_list, expanded_account=account_id)
        elif type == 'ns_company_id':
            query, params = self._get_query_sums_company(options_list, expanded_account=account_id)
        elif type == 'undefined':
            query, params = self._get_query_sums_undefined(options_list, expanded_account=account_id)

        groupby_accounts = {}
        groupby_companies = {}
        groupby_taxes = {}

        self._cr_execute(options_list[0], query, params)
        for res in self._cr.dictfetchall():
            i = res['period_number']
            key = res['key']
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_accounts[res['groupby']][i][key] = res
            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_accounts[res['groupby']][i][key] = res
            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_companies[res['groupby']][i] = res
            elif key == 'base_amount' and len(options_list) == 1:
                groupby_taxes.setdefault(res['groupby'], {})
                groupby_taxes[res['groupby']][key] = res['balance']
            elif key == 'tax_amount' and len(options_list) == 1:
                groupby_taxes.setdefault(res['groupby'], {})
                groupby_taxes[res['groupby']][key] = res['balance']

        # Fetch the lines of unfolded accounts.
        # /!\ Unfolding lines combined with multiple comparisons is not supported.
        if fetch_lines and len(options_list) == 1:
            options = options_list[0]
            unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
            if expanded_account or unfold_all or options['unfolded_lines']:
                query, params = self._get_query_amls(options, expanded_account)
                self._cr_execute(options, query, params)
                for res in self._cr.dictfetchall():
                    groupby_accounts[res['account_id']][0].setdefault('lines', [])
                    groupby_accounts[res['account_id']][0]['lines'].append(res)

        # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
        # There is an unaffected earnings for each company but it's less costly to fetch all candidate accounts in
        # a single search and then iterate it.
        if groupby_companies:
            unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
            candidates_accounts = self.env['account.account'].search([
                ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', 'in', list(groupby_companies.keys()))
            ])
            for account in candidates_accounts:
                company_unaffected_earnings = groupby_companies.get(account.company_id.id)
                if not company_unaffected_earnings:
                    continue
                for i in range(len(options_list)):
                    unaffected_earnings = company_unaffected_earnings[i]
                    groupby_accounts.setdefault(account.id, [{} for i in range(len(options_list))])
                    groupby_accounts[account.id][i]['unaffected_earnings'] = unaffected_earnings
                del groupby_companies[account.company_id.id]

        # Retrieve the accounts to browse.
        # groupby_accounts.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # - the unaffected earnings allocation.
        # Note a search is done instead of a browse to preserve the table ordering.
        accounts = self.env['account.analytic.account'].search([('id', 'in', list(groupby_accounts.keys()))])
        accounts_results = [(account, groupby_accounts[account.id]) for account in accounts]
        
        if None in groupby_accounts.keys():
            accounts_results.append((self.env['account.analytic.account'],groupby_accounts[None]))

        # Fetch as well the taxes.
        if groupby_taxes:
            taxes = self.env['account.tax'].search([('id', 'in', list(groupby_taxes.keys()))])
        else:
            taxes = []
        taxes_results = [(tax, groupby_taxes[tax.id]) for tax in taxes]
        return accounts_results, taxes_results


    @api.model
    def _get_options_sum_balance(self, options):
        return self.env['account.general.ledger']._get_options_sum_balance(options)


    @api.model
    def _get_options_unaffected_earnings(self, options):
        return self.env['account.general.ledger']._get_options_unaffected_earnings(options)

    @api.model
    def _get_options_initial_balance(self, options):
        return self.env['account.general.ledger']._get_options_initial_balance(options)