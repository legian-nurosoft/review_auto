# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"


    @api.model
    def _get_columns_name(self, options):
        columns_names = [
            {'name': ''},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Communication')},
            {'name': _('Partner')},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'}
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns_names.insert(4, {'name': _('Currency'), 'class': 'number'})

        if options.get('show_usd_real',False):
            columns_names.insert(4, {'name': _('Balance USD Real'), 'class': 'number'})
            columns_names.insert(4, {'name': _('Credit USD Real'), 'class': 'number'})
            columns_names.insert(4, {'name': _('Debit USD Real'), 'class': 'number'})

        if options.get('show_usd_budget',False):
            columns_names.insert(4, {'name': _('Balance USD Budget'), 'class': 'number'})
            columns_names.insert(4, {'name': _('Credit USD Budget'), 'class': 'number'})
            columns_names.insert(4, {'name': _('Debit USD Budget'), 'class': 'number'})

        return columns_names

    @api.model
    def _get_query_sums(self, options_list, expanded_account=None):
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
                    account_move_line.account_id                            AS groupby,
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
                WHERE %s
                GROUP BY account_move_line.account_id
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
                        account_move_line.account_id                            AS groupby,
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
                    WHERE %s
                    GROUP BY account_move_line.account_id
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
    def _get_query_amls(self, options, expanded_account, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_account:    The account.account record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''

        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._force_strict_range(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env['res.currency']._get_query_currency_table(options)
        query = '''
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line.ns_debit_usd_budget   AS debit_budget,
                account_move_line.ns_credit_usd_budget  AS credit_budget,
                account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget AS balance_budget,
                account_move_line.ns_debit_usd_real   AS debit_real,
                account_move_line.ns_credit_usd_real  AS credit_real,
                account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real AS balance_real,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.move_type         AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name
            FROM account_move_line
            LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            WHERE %s
            ORDER BY account_move_line.date, account_move_line.id
        ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    @api.model
    def _get_account_title_line(self, options, account, amount_currency, debit, credit, balance, has_lines, debit_real=0, credit_real=0, balance_real=0, debit_budget=0,credit_budget=0,balance_budget=0):
        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')

        name = '%s %s' % (account.code, account.name)
        max_length = self._context.get('print_mode') and 100 or 60
        if len(name) > max_length and not self._context.get('no_format'):
            name = name[:max_length] + '...'
        columns = [
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': has_foreign_currency and self.format_value(amount_currency, currency=account.currency_id, blank_if_zero=True) or '', 'class': 'number'})
        
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        if options.get('show_usd_real',False):
            columns_real = [
                {'name': self.format_value(debit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_real, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_real + columns

        if options.get('show_usd_budget',False):
            columns_budget = [
                {'name': self.format_value(debit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_budget, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_budget + columns

        return {
            'id': 'account_%d' % account.id,
            'name': name,
            'title_hover': name,
            'columns': columns,
            'level': 2,
            'unfoldable': has_lines,
            'unfolded': has_lines and 'account_%d' % account.id in options.get('unfolded_lines') or unfold_all,
            'colspan': 4,
            'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
        }

    @api.model
    def _get_initial_balance_line(self, options, account, amount_currency, debit, credit, balance, debit_real=0, credit_real=0, balance_real=0, debit_budget=0,credit_budget=0,balance_budget=0):
        columns = [
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]

        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': has_foreign_currency and self.format_value(amount_currency, currency=account.currency_id, blank_if_zero=True) or '', 'class': 'number'})
        
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        if options.get('show_usd_real',False):
            columns_real = [
                {'name': self.format_value(debit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_real, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_real + columns

        if options.get('show_usd_budget',False):
            columns_budget = [
                {'name': self.format_value(debit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_budget, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_budget + columns

        return {
            'id': 'initial_%d' % account.id,
            'class': 'o_account_reports_initial_balance',
            'name': _('Initial Balance'),
            'parent_id': 'account_%d' % account.id,
            'columns': columns,
            'colspan': 4,
        }


    @api.model
    def _get_total_line(self, options, debit, credit, balance, debit_real=0, credit_real=0, balance_real=0, debit_budget=0,credit_budget=0,balance_budget=0):
        result = {
            'id': 'general_ledger_total_%s' % self.env.company.id,
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': [
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': self.user_has_groups('base.group_multi_currency') and 5 or 4,
        }

        columns_real = []
        columns_budget = []

        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)

        if options.get('show_usd_real',False):
            columns_real = [
                {'name': self.format_value(debit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_real, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_real, currency=usd_currency), 'class': 'number'},
            ]

        if options.get('show_usd_budget',False):
            columns_budget = [
                {'name': self.format_value(debit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(credit_budget, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(balance_budget, currency=usd_currency), 'class': 'number'},
            ]

        if options.get('show_usd_real',False) or options.get('show_usd_budget',False):
            columns_extra = []
            if self.user_has_groups('base.group_multi_currency'):
                columns_extra = [
                    {'name': '', 'class': 'number'},
                ]

                result['colspan'] = result['colspan'] - 1

            result['columns'] = columns_real + columns_budget + columns_extra + result['columns']

        return result

    @api.model
    def _get_aml_line(self, options, account, aml, cumulated_balance, cumulated_balance_real=0, cumulated_balance_budget=0):
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        if aml['ref'] and aml['name']:
            title = '%s - %s' % (aml['name'], aml['ref'])
        elif aml['ref']:
            title = aml['ref']
        elif aml['name']:
            title = aml['name']
        else:
            title = ''

        if (aml['currency_id'] and aml['currency_id'] != account.company_id.currency_id.id) or account.currency_id:
            currency = self.env['res.currency'].browse(aml['currency_id'])
        else:
            currency = False

        columns = [
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': currency and aml['amount_currency'] and self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True) or '', 'class': 'number'})
        
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        if options.get('show_usd_real',False):
            columns_real = [
                {'name': self.format_value(aml['debit_real'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(aml['credit_real'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(cumulated_balance_real, blank_if_zero=True, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_real + columns

        if options.get('show_usd_budget',False):
            columns_budget = [
                {'name': self.format_value(aml['debit_budget'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(aml['credit_budget'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(cumulated_balance_budget, blank_if_zero=True, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_budget + columns

        first_columns = [
            {'name': format_date(self.env, aml['date']), 'class': 'date'},
            {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name']), 'title': title, 'class': 'whitespace_print o_account_report_line_ellipsis'},
            {'name': aml['partner_name'], 'title': aml['partner_name'], 'class': 'whitespace_print'}
        ]

        columns = first_columns + columns

        return {
            'id': aml['id'],
            'caret_options': caret_type,
            'class': 'top-vertical-align',
            'parent_id': 'account_%d' % aml['account_id'],
            'name': aml['move_name'],
            'columns': columns,
            'level': 2,
        }

    @api.model
    def _get_general_ledger_lines(self, options, line_id=None):
        ''' Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []
        aml_lines = []
        options_list = self._get_options_periods_list(options)
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        expanded_account = line_id and self.env['account.account'].browse(int(line_id[8:]))
        accounts_results, taxes_results = self._do_query(options_list, expanded_account=expanded_account)

        total_debit = total_credit = total_balance = 0.0
        total_debit_budget = total_credit_budget = total_balance_budget = 0.0
        total_debit_real = total_credit_real = total_balance_real = 0.0
        for account, periods_results in accounts_results:
            # No comparison allowed in the General Ledger. Then, take only the first period.
            results = periods_results[0]

            is_unfolded = 'account_%s' % account.id in options['unfolded_lines']

            # account.account record line.
            account_sum = results.get('sum', {})
            account_un_earn = results.get('unaffected_earnings', {})

            # Check if there is sub-lines for the current period.
            max_date = account_sum.get('max_date')
            has_lines = max_date and max_date >= date_from or False

            amount_currency = account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0)
            debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
            credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
            balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

            debit_budget = account_sum.get('debit_budget', 0.0) + account_un_earn.get('debit_budget', 0.0)
            credit_budget = account_sum.get('credit_budget', 0.0) + account_un_earn.get('credit_budget', 0.0)
            balance_budget = account_sum.get('balance_budget', 0.0) + account_un_earn.get('balance_budget', 0.0)

            debit_real = account_sum.get('debit_real', 0.0) + account_un_earn.get('debit_real', 0.0)
            credit_real = account_sum.get('credit_real', 0.0) + account_un_earn.get('credit_real', 0.0)
            balance_real = account_sum.get('balance_real', 0.0) + account_un_earn.get('balance_real', 0.0)

            lines.append(self._get_account_title_line(options, account, amount_currency, debit, credit, balance, has_lines, debit_real=debit_real, credit_real=credit_real, balance_real=balance_real, debit_budget=debit_budget,credit_budget=credit_budget, balance_budget=balance_budget))

            total_debit += debit
            total_credit += credit
            total_balance += balance

            total_debit_real += debit_real
            total_credit_real += credit_real
            total_balance_real += balance_real

            total_debit_budget += debit_budget
            total_credit_budget += credit_budget
            total_balance_budget += balance_budget

            if has_lines and (unfold_all or is_unfolded):
                # Initial balance line.
                account_init_bal = results.get('initial_balance', {})

                cumulated_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                cumulated_balance_real = account_init_bal.get('balance_real', 0.0) + account_un_earn.get('balance_real', 0.0)
                cumulated_balance_budget = account_init_bal.get('balance_budget', 0.0) + account_un_earn.get('balance_budget', 0.0)

                lines.append(self._get_initial_balance_line(
                    options, account,
                    account_init_bal.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    account_init_bal.get('debit', 0.0) + account_un_earn.get('debit', 0.0),
                    account_init_bal.get('credit', 0.0) + account_un_earn.get('credit', 0.0),
                    cumulated_balance,
                    debit_real=account_init_bal.get('debit_real', 0.0) + account_un_earn.get('debit_real', 0.0),
                    credit_real=account_init_bal.get('credit_real', 0.0) + account_un_earn.get('credit_real', 0.0),
                    balance_real=account_init_bal.get('balance_real', 0.0) + account_un_earn.get('balance_real', 0.0),
                    debit_budget=account_init_bal.get('debit_budget', 0.0) + account_un_earn.get('debit_budget', 0.0),
                    credit_budget=account_init_bal.get('credit_budget', 0.0) + account_un_earn.get('credit_budget', 0.0),
                    balance_budget=account_init_bal.get('balance_budget', 0.0) + account_un_earn.get('balance_budget', 0.0)
                ))

                # account.move.line record lines.
                amls = results.get('lines', [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES

                for aml in amls:
                    # Don't show more line than load_more_counter.
                    if load_more_counter == 0:
                        break

                    cumulated_balance += aml['balance']
                    cumulated_balance_real += aml['balance_real']
                    cumulated_balance_budget += aml['balance_budget']
                    lines.append(self._get_aml_line(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget))
                    
                    a_move_line = self.env['account.move.line'].browse(aml['id'])
                    has_undefined_analytic = True
                    
                    if a_move_line.analytic_account_id:
                        has_undefined_analytic = False
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.analytic_account_id))

                    if a_move_line.ns_cost_center_id:
                        has_undefined_analytic = False
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.ns_cost_center_id))

                    if a_move_line.ns_site_id:
                        has_undefined_analytic = False
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.ns_site_id))

                    if a_move_line.ns_project_id:
                        has_undefined_analytic = False
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.ns_project_id))

                    if a_move_line.ns_company_id:
                        has_undefined_analytic = False
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.ns_company_id))

                    if has_undefined_analytic:
                        lines.append(self._get_aml_line_analytic(options, account, aml, company_currency.round(cumulated_balance), cumulated_balance_real=cumulated_balance_real, cumulated_balance_budget=cumulated_balance_budget, analytic_account_id=a_move_line.analytic_account_id))

                    load_more_remaining -= 1
                    load_more_counter -= 1
                    aml_lines.append(aml['id'])

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(self._get_load_more_line(
                        options, account,
                        self.MAX_LINES,
                        load_more_remaining,
                        cumulated_balance,
                    ))

                if self.env.company.totals_below_sections:
                    # Account total line.
                    lines.append(self._get_account_total_line(
                        options, account,
                        account_sum.get('amount_currency', 0.0),
                        account_sum.get('debit', 0.0),
                        account_sum.get('credit', 0.0),
                        account_sum.get('balance', 0.0),
                    ))

        if not line_id:
            # Report total line.
            lines.append(self._get_total_line(
                options,
                total_debit,
                total_credit,
                company_currency.round(total_balance),
                debit_real=total_debit_real, 
                credit_real=total_credit_real, 
                balance_real=total_balance_real, 
                debit_budget=total_debit_budget,
                credit_budget=total_credit_budget, 
                balance_budget=total_balance_budget
            ))

            # Tax Declaration lines.
            journal_options = self._get_options_journals(options)
            if len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
                lines += self._get_tax_declaration_lines(
                    options, journal_options[0]['type'], taxes_results
                )
        if self.env.context.get('aml_only'):
            return aml_lines
        return lines


    @api.model
    def _get_aml_line_analytic(self, options, account, aml, cumulated_balance, cumulated_balance_real=0, cumulated_balance_budget=0, analytic_account_id=False):
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        if aml['ref'] and aml['name']:
            title = '%s - %s' % (aml['name'], aml['ref'])
        elif aml['ref']:
            title = aml['ref']
        elif aml['name']:
            title = aml['name']
        else:
            title = ''

        if (aml['currency_id'] and aml['currency_id'] != account.company_id.currency_id.id) or account.currency_id:
            currency = self.env['res.currency'].browse(aml['currency_id'])
        else:
            currency = False

        columns = [
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': currency and aml['amount_currency'] and self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True) or '', 'class': 'number'})
        
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)
        if options.get('show_usd_real',False):
            columns_real = [
                {'name': self.format_value(aml['debit_real'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(aml['credit_real'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(cumulated_balance_real, blank_if_zero=True, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_real + columns

        if options.get('show_usd_budget',False):
            columns_budget = [
                {'name': self.format_value(aml['debit_budget'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(aml['credit_budget'], blank_if_zero=True, currency=usd_currency), 'class': 'number'},
                {'name': self.format_value(cumulated_balance_budget, blank_if_zero=True, currency=usd_currency), 'class': 'number'},
            ]

            columns = columns_budget + columns

        first_columns = [
            {'name': '', 'class': 'whitespace_print'},
            {'name': '', 'class': 'whitespace_print'},
            {'name': '', 'class': 'whitespace_print'},
        ]

        columns = first_columns + columns

        return {
            'id': aml['id'],
            'ns_analytic_id': analytic_account_id.id if analytic_account_id else -99,
            'class': 'top-vertical-align',
            'parent_id': 'account_%d' % aml['account_id'],
            'name': analytic_account_id.display_name if analytic_account_id else 'Undefined',
            'columns': columns,
            'level': 4,
        }


    