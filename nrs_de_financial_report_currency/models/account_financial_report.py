# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
from collections import defaultdict
from odoo.exceptions import UserError

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_show_usd_budget = False
    filter_show_usd_real = False
    filter_show_ifrs = False
    filter_show_gaap = False     

    @api.model
    def _get_options_analytic_domain(self, options):
        domain = []
        if options.get('analytic_accounts'):
            analytic_account_ids = [int(acc) for acc in options['analytic_accounts']]
            domain.append(('analytic_account_id', 'in', analytic_account_ids))
            domain = expression.OR([domain, [('ns_cost_center_id', 'in', analytic_account_ids)]])
            domain = expression.OR([domain, [('ns_site_id', 'in', analytic_account_ids)]])
            domain = expression.OR([domain, [('ns_project_id', 'in', analytic_account_ids)]])
            domain = expression.OR([domain, [('ns_company_id', 'in', analytic_account_ids)]])
        if options.get('analytic_tags'):
            analytic_tag_ids = [int(tag) for tag in options['analytic_tags']]
            domain.append(('analytic_tag_ids', 'in', analytic_tag_ids))
        return domain

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountReport, self)._get_options_domain(options)

        ifrs_gaap_domain = []
        if options.get('show_ifrs', False):
            ifrs_gaap_domain = expression.OR([ifrs_gaap_domain, [('ns_fr','=','IFRS')]])

        if options.get('show_gaap', False):
            ifrs_gaap_domain = expression.OR([ifrs_gaap_domain, [('ns_fr','=','GAAP')]])

        if len(ifrs_gaap_domain) > 0:
            ifrs_gaap_domain = expression.OR([ifrs_gaap_domain, [('ns_fr','=',False)]])
            domain = expression.AND([domain, ifrs_gaap_domain])

        return domain


    @api.model
    def _create_hierarchy(self, lines, options):
        """Compute the hierarchy based on account groups when the option is activated.

        The option is available only when there are account.group for the company.
        It should be called when before returning the lines to the client/templater.
        The lines are the result of _get_lines(). If there is a hierarchy, it is left
        untouched, only the lines related to an account.account are put in a hierarchy
        according to the account.group's and their prefixes.
        """
        unfold_all = self.env.context.get('print_mode') and len(options.get('unfolded_lines')) == 0 or options.get('unfold_all')

        def add_to_hierarchy(lines, key, level, parent_id, hierarchy):
            val_dict = hierarchy[key]
            unfolded = val_dict['id'] in options.get('unfolded_lines') or unfold_all
            # add the group totals
            lines.append({
                'id': val_dict['id'],
                'name': val_dict['name'],
                'title_hover': val_dict['name'],
                'unfoldable': True,
                'unfolded': unfolded,
                'level': level,
                'parent_id': parent_id,
                'columns': [{'name': self.format_value(c) if isinstance(c, (int, float)) else c, 'no_format_name': c} for c in val_dict['totals']],
                'name_class': 'o_account_report_name_ellipsis top-vertical-align'
            })
            
            if not self._context.get('print_mode') or unfolded:
                # add every direct child group recursively
                children = []
                for child in sorted(val_dict['children_codes']):
                    add_to_hierarchy(children, child, level + 1, val_dict['id'], hierarchy)
                # add all the lines that are in this group but not in one of this group's children groups
                for l in val_dict['lines']:
                    if l.get('ns_analytic_account_id'):
                        l['level'] = level + 3
                        l['parent_id'] = l['parent_id']
                    else:
                        l['level'] = level + 1
                        l['parent_id'] = val_dict['id']
                
                lines.extend(val_dict['lines'] + children)
                

        def compute_hierarchy(lines, level, parent_id):
            # put every line in each of its parents (from less global to more global) and compute the totals
            hierarchy = defaultdict(lambda: {'totals': [None] * len(lines[0]['columns']), 'lines': [], 'children_codes': set(), 'name': '', 'parent_id': None, 'id': ''})
            
            for line in lines:
                if not line.get('ns_analytic_account_id'):
                    account = self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('id'))))
                    codes = self.get_account_codes(account)  # id, name

                    for code in codes:
                        hierarchy[code[0]]['id'] = 'hierarchy_' + str(code[0])
                        hierarchy[code[0]]['name'] = code[1]
                        for i, column in enumerate(line['columns']):
                            if 'no_format_name' in column:
                                no_format = column['no_format_name']
                            elif 'no_format' in column:
                                no_format = column['no_format']
                            else:
                                no_format = None
                            if isinstance(no_format, (int, float)):
                                if hierarchy[code[0]]['totals'][i] is None:
                                    hierarchy[code[0]]['totals'][i] = no_format
                                else:
                                    hierarchy[code[0]]['totals'][i] += no_format
                    
                    for code, child in zip(codes[:-1], codes[1:]):
                        hierarchy[code[0]]['children_codes'].add(child[0])
                        hierarchy[child[0]]['parent_id'] = hierarchy[code[0]]['id']
                    hierarchy[codes[-1][0]]['lines'] += [line]
                else:
                    account = self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('parent_id'))))
                    codes = self.get_account_codes(account)  # id, name
                    hierarchy[codes[-1][0]]['lines'] += [line]
            
            # compute the tree-like structure by starting at the roots (being groups without parents)
            hierarchy_lines = []
            for root in [k for k, v in hierarchy.items() if not v['parent_id']]:
                add_to_hierarchy(hierarchy_lines, root, level, parent_id, hierarchy)
            
            return hierarchy_lines

        new_lines = []
        account_lines = []
        current_level = 0
        parent_id = 'root'
        for line in lines:
            if not (line.get('caret_options') == 'account.account' or line.get('account_id') or line.get('ns_analytic_account_id')):
                # make the hierarchy with the lines we gathered, append it to the new lines and restart the gathering
                if account_lines:
                    new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
                account_lines = []
                new_lines.append(line)
                current_level = line['level']
                parent_id = line['id']
            else:
                # gather all the lines we can create a hierarchy on
                account_lines.append(line)
        # do it one last time for the gathered lines remaining
        if account_lines:
            new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
        return new_lines

class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"    

    @property
    def filter_show_usd_budget(self):
        if self.ns_show_usd_budget:
            return False
        else:
            return None

    @property
    def filter_show_usd_real(self):
        if self.ns_show_usd_real:
            return False
        else:
            return None

    @property
    def filter_show_ifrs(self):
        if self.ns_show_ifrs:
            return False
        else:
            return None

    @property
    def filter_show_gaap(self):
        if self.ns_show_gaap:
            return False
        else:
            return None

    ns_show_usd_budget = fields.Boolean(string='Show USD Budget', default=False)
    ns_show_usd_real = fields.Boolean(string='Show USD Real', default=False)
    ns_show_ifrs = fields.Boolean(string='Show IFRS', default=False)
    ns_show_gaap = fields.Boolean(string='Show GAAP', default=False)


    @api.model
    def _build_headers_hierarchy(self, options_list, groupby_keys):
        headers, sorted_groupby_keys = super(ReportAccountFinancialReport, self)._build_headers_hierarchy(options_list, groupby_keys)
                
        if options_list[0].get('show_usd_real',False):
            for i in range(len(headers)):
                if i == 0:
                    new_headers = []
                    for j in range(len(headers[i])):
                        if len(headers[i][j].get('name','')) >= 2:                            
                            new_headers.append({
                                'name': headers[i][j]['name'] + ' ' + _('USD Real'),
                                'style': 'width: 1%; text-align: right;',
                            })
                    
                    for k in range(len(new_headers),-1,-1):
                        if k -1 >= 0:
                            headers[i].insert(1,new_headers[k-1])
                else:
                    headers[i].insert(1,{'name': '', 'style': 'width: 1%; text-align: right;'})

        if options_list[0].get('show_usd_budget',False):
            for i in range(len(headers)):
                if i == 0:
                    new_headers = []
                    for j in range(len(headers[i])):
                        if len(headers[i][j].get('name','')) >= 2 and _('USD Real') not in headers[i][j].get('name',''):                            
                            new_headers.append({
                                'name': headers[i][j]['name'] + ' ' + _('USD Budget'),
                                'style': 'width: 1%; text-align: right;',
                            })
                    
                    for k in range(len(new_headers),-1,-1):
                        if k -1 >= 0:
                            headers[i].insert(1,new_headers[k-1])
                else:
                    headers[i].insert(1,{'name': '', 'style': 'width: 1%; text-align: right;'})

        return headers, sorted_groupby_keys

    @api.model
    def _get_financial_line_report_line(self, options, financial_line, solver, groupby_keys):
        res = super(ReportAccountFinancialReport, self)._get_financial_line_report_line(options, financial_line, solver, groupby_keys)
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)

        if options.get('show_usd_real',False):
            results = solver.get_results_real(financial_line)['formula_real']
            new_column = []
            for key in groupby_keys:
                amount = results.get(key, 0.0)
                new_column.append({'name': self._format_cell_value(financial_line, amount, currency=usd_currency), 'no_format': amount, 'class': 'number'})

            for k in range(len(new_column),-1,-1):
                if k -1 >= 0:
                    res['columns'].insert(0,new_column[k-1])
        
        if options.get('show_usd_budget',False):
            results = solver.get_results_budget(financial_line)['formula_budget']
            new_column = []
            for key in groupby_keys:
                amount = results.get(key, 0.0)
                new_column.append({'name': self._format_cell_value(financial_line, amount, currency=usd_currency), 'no_format': amount, 'class': 'number'})

            for k in range(len(new_column),-1,-1):
                if k -1 >= 0:
                    res['columns'].insert(0,new_column[k-1])
        return res

    @api.model
    def _get_financial_aml_report_line_budget(self, options, financial_line, groupby_id, display_name, results, groupby_keys): 
        columns = []       
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)        
        for key in groupby_keys:
            amount = results.get(key, 0.0)
            columns.append({'name': self._format_cell_value(financial_line, amount, currency=usd_currency), 'no_format': amount, 'class': 'number'})

        return columns

    @api.model
    def _get_financial_aml_report_line_real(self, options, financial_line, groupby_id, display_name, results, groupby_keys): 
        columns = []       
        usd_currency = self.env['res.currency'].search([('name','=','USD')],limit=1)        
        for key in groupby_keys:
            amount = results.get(key, 0.0)
            columns.append({'name': self._format_cell_value(financial_line, amount, currency=usd_currency), 'no_format': amount, 'class': 'number'})

        return columns

    @api.model
    def _build_lines_hierarchy(self, options_list, financial_lines, solver, groupby_keys):
        ''' Travel the whole hierarchy and create the report lines to be rendered.
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param financial_lines:     An account.financial.html.report.line recordset.
        :param solver:              The FormulaSolver instance used to compute the formulas.
        :param groupby_keys:        The sorted encountered keys in the solver.
        :return:                    The lines.
        '''
        lines = []
        for financial_line in financial_lines:

            is_leaf = solver.is_leaf(financial_line)
            has_lines = solver.has_move_lines(financial_line)

            financial_report_line = self._get_financial_line_report_line(
                options_list[0],
                financial_line,
                solver,
                groupby_keys,
            )

            # Manage 'hide_if_zero' field.
            if financial_line.hide_if_zero and all(self.env.company.currency_id.is_zero(column['no_format'])
                                                   for column in financial_report_line['columns'] if 'no_format' in column):
                continue

            # Manage 'hide_if_empty' field.
            if financial_line.hide_if_empty and is_leaf and not has_lines:
                continue

            lines.append(financial_report_line)

            aml_lines = []            
            if financial_line.children_ids:
                # Travel children.
                lines += self._build_lines_hierarchy(options_list, financial_line.children_ids, solver, groupby_keys)
            elif is_leaf and financial_report_line['unfolded']:
                # Fetch the account.move.lines.
                solver_results = solver.get_results(financial_line)
                sign = solver_results['amls']['sign']                

                for groupby_id, display_name, results in financial_line._compute_amls_results(options_list, self, sign=sign):
                    parent_groupby_id = groupby_id

                    current_line = self._get_financial_aml_report_line(
                        options_list[0],
                        financial_line,
                        groupby_id,
                        display_name,
                        results,
                        groupby_keys,
                    )

                    budget_columns = []
                    if options_list[0].get('show_usd_budget',False):
                        for groupby_id, display_name, results in financial_line._compute_amls_results_budget(options_list, self, sign=sign, parent_groupby_id=parent_groupby_id):
                            budget_columns = self._get_financial_aml_report_line_budget(
                                options_list[0],
                                financial_line,
                                groupby_id,
                                display_name,
                                results,
                                groupby_keys,
                            )

                    real_columns = []
                    if options_list[0].get('show_usd_real',False):
                        for groupby_id, display_name, results in financial_line._compute_amls_results_real(options_list, self, sign=sign, parent_groupby_id=parent_groupby_id):
                            real_columns = self._get_financial_aml_report_line_real(
                                options_list[0],
                                financial_line,
                                groupby_id,
                                display_name,
                                results,
                                groupby_keys,
                            )
                    
                    current_line['columns'] = budget_columns + real_columns + current_line['columns']
                    aml_lines.append(current_line)                   
                    
                    for groupby_id, display_name, results in financial_line._compute_amls_results_analytic(options_list, self, sign=sign, parent_groupby_id=parent_groupby_id):
                        current_analytic_account_id = groupby_id

                        current_analytic_line = self._get_financial_aml_report_line_analytic(
                            options_list[0],
                            financial_line,
                            groupby_id,
                            display_name,
                            results,
                            groupby_keys,
                            parent_groupby_id,
                        )

                        budget_columns_analytic = []
                        if options_list[0].get('show_usd_budget',False):
                            for groupby_id, display_name, results in financial_line._compute_amls_results_budget_analytic(options_list, self, sign=sign, parent_groupby_id=parent_groupby_id, analytic_account_id=current_analytic_account_id):
                                budget_columns_analytic = self._get_financial_aml_report_line_budget(
                                    options_list[0],
                                    financial_line,
                                    groupby_id,
                                    display_name,
                                    results,
                                    groupby_keys,
                                )

                        real_columns_analytic = []
                        if options_list[0].get('show_usd_real',False):
                            for groupby_id, display_name, results in financial_line._compute_amls_results_real_analytic(options_list, self, sign=sign, parent_groupby_id=parent_groupby_id, analytic_account_id=current_analytic_account_id):
                                real_columns_analytic = self._get_financial_aml_report_line_real(
                                    options_list[0],
                                    financial_line,
                                    groupby_id,
                                    display_name,
                                    results,
                                    groupby_keys,
                                )
                        
                        current_analytic_line['columns'] = budget_columns_analytic + real_columns_analytic + current_analytic_line['columns']

                        aml_lines.append(current_analytic_line)

            lines += aml_lines

            if self.env.company.totals_below_sections and (financial_line.children_ids or (is_leaf and financial_report_line['unfolded'] and aml_lines)):
                lines.append(self._get_financial_total_section_report_line(options_list[0], financial_report_line))
                financial_report_line["unfolded"] = True  # enables adding "o_js_account_report_parent_row_unfolded" -> hides total amount in head line as it is displayed later in total line

        return lines

    @api.model
    def _get_financial_aml_report_line_analytic(self, options, financial_line, groupby_id, display_name, results, groupby_keys, parent_groupby_id):
        ''' Create the report line for the account.move.line grouped by any key.
        :param options:             The report options.
        :param financial_line:      An account.financial.html.report.line record.
        :param groupby_id:          The key used as the vertical group_by. It could be a record's id or a value for regular field.
        :param display_name:        The full name of the line to display.
        :param results:             The results given by the FormulaSolver class for the given line.
        :param groupby_keys:        The sorted encountered keys in the solver.
        :return:                    The dictionary corresponding to a line to be rendered.
        '''
        # Standard columns.
        columns = []
        if groupby_id == None:
            groupby_id = -99

        for key in groupby_keys:
            amount = results.get(key, 0.0)
            columns.append({'name': self._format_cell_value(financial_line, amount), 'no_format': amount, 'class': 'number'})

        # Growth comparison column.
        if self._display_growth_comparison(options):
            columns.append(self._compute_growth_comparison_column(options,
                columns[0]['no_format'],
                columns[1]['no_format'],
                green_on_positive=financial_line.green_on_positive
            ))

        if self._display_debug_info(options):
            columns.append({'name': '', 'style': 'width: 1%;'})

        return {
            'id': 'ns_analytic_account_id_%s' % (groupby_id),
            'name': display_name,
            'level': financial_line.level + 2,
            'parent_id': 'financial_report_group_%s_%s' % (financial_line.id, parent_groupby_id),
            'ns_analytic_account_id': groupby_id,
            'columns': columns,
        }

class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _compute_amls_results_analytic(self, options_list, calling_financial_report=None, sign=1, parent_groupby_id=0):
        ''' Compute the results for the unfolded lines by taking care about the line order and the group by filter.

        Suppose the line has '-sum' as formulas with 'partner_id' in groupby and 'currency_id' in group by filter.
        The result will be something like:
        [
            (0, 'partner 0', {(0,1): amount1, (0,2): amount2, (1,1): amount3}),
            (1, 'partner 1', {(0,1): amount4, (0,2): amount5, (1,1): amount6}),
            ...               |
        ]    |                |
             |__ res.partner ids
                              |_ key where the first element is the period number, the second one being a res.currency id.

        :param options_list:                The report options list, first one being the current dates range, others
                                            being the comparisons.
        :param calling_financial_report:    The financial report called by the user to be rendered.
        :param sign:                        1 or -1 to get negative values in case of '-sum' formula.
        :return:                            A list (groupby_key, display_name, {key: <balance>...}).
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = ['analytic_account_id','ns_cost_center_id','ns_site_id','ns_project_id','ns_company_id'] + horizontal_groupby_list
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        groupby_field = self.env['account.move.line']._fields['analytic_account_id']        

        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)
            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COALESCE(SUM(ROUND(%s * account_move_line.balance * currency_table.rate, currency_table.precision)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + ''' AND account_move_line.account_id = ''' + str(parent_groupby_id) + ' ' + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params += [i, sign] + where_params

        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}

        parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            has_undefined_analytic = True            

            if res['analytic_account_id']:
                has_undefined_analytic = False
                results.setdefault(res['analytic_account_id'], {})
                results[res['analytic_account_id']][key] = res['balance']
            
            if res['ns_cost_center_id']:
                has_undefined_analytic = False
                results.setdefault(res['ns_cost_center_id'], {})
                results[res['ns_cost_center_id']][key] = res['balance']

            if res['ns_site_id']:
                has_undefined_analytic = False
                results.setdefault(res['ns_site_id'], {})
                results[res['ns_site_id']][key] = res['balance']

            if res['ns_project_id']:
                has_undefined_analytic = False
                results.setdefault(res['ns_project_id'], {})
                results[res['ns_project_id']][key] = res['balance']

            if res['ns_company_id']:
                has_undefined_analytic = False
                results.setdefault(res['ns_company_id'], {})
                results[res['ns_company_id']][key] = res['balance']

            if has_undefined_analytic:
                results.setdefault(res['analytic_account_id'], {})
                results[res['analytic_account_id']][key] = res['balance']

        
        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
            
            if None in results.keys():
                sorted_values.append((None, 'Undefined'))
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]


    def _compute_amls_results_budget(self, options_list, calling_financial_report=None, sign=1, parent_groupby_id=0):
        ''' Compute the results for the unfolded lines by taking care about the line order and the group by filter.

        Suppose the line has '-sum' as formulas with 'partner_id' in groupby and 'currency_id' in group by filter.
        The result will be something like:
        [
            (0, 'partner 0', {(0,1): amount1, (0,2): amount2, (1,1): amount3}),
            (1, 'partner 1', {(0,1): amount4, (0,2): amount5, (1,1): amount6}),
            ...               |
        ]    |                |
             |__ res.partner ids
                              |_ key where the first element is the period number, the second one being a res.currency id.

        :param options_list:                The report options list, first one being the current dates range, others
                                            being the comparisons.
        :param calling_financial_report:    The financial report called by the user to be rendered.
        :param sign:                        1 or -1 to get negative values in case of '-sum' formula.
        :return:                            A list (groupby_key, display_name, {key: <balance>...}).
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = [self.groupby] + horizontal_groupby_list
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        groupby_field = self.env['account.move.line']._fields[self.groupby]

        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COALESCE(SUM(%s * (account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + ''' AND account_move_line.account_id = ''' + str(parent_groupby_id) + ' ' + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params += [i, sign] + where_params

        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}

        parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            results.setdefault(res[self.groupby], {})
            results[res[self.groupby]][key] = res['balance']

        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]


    def _compute_amls_results_real(self, options_list, calling_financial_report=None, sign=1, parent_groupby_id=0):
        ''' Compute the results for the unfolded lines by taking care about the line order and the group by filter.

        Suppose the line has '-sum' as formulas with 'partner_id' in groupby and 'currency_id' in group by filter.
        The result will be something like:
        [
            (0, 'partner 0', {(0,1): amount1, (0,2): amount2, (1,1): amount3}),
            (1, 'partner 1', {(0,1): amount4, (0,2): amount5, (1,1): amount6}),
            ...               |
        ]    |                |
             |__ res.partner ids
                              |_ key where the first element is the period number, the second one being a res.currency id.

        :param options_list:                The report options list, first one being the current dates range, others
                                            being the comparisons.
        :param calling_financial_report:    The financial report called by the user to be rendered.
        :param sign:                        1 or -1 to get negative values in case of '-sum' formula.
        :return:                            A list (groupby_key, display_name, {key: <balance>...}).
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = [self.groupby] + horizontal_groupby_list
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        groupby_field = self.env['account.move.line']._fields[self.groupby]

        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COALESCE(SUM(%s * (account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + ''' AND account_move_line.account_id = ''' + str(parent_groupby_id) + ' ' + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params += [i, sign] + where_params

        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}

        parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            results.setdefault(res[self.groupby], {})
            results[res[self.groupby]][key] = res['balance']

        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]


    def _compute_amls_results_budget_analytic(self, options_list, calling_financial_report=None, sign=1, parent_groupby_id=0, analytic_account_id=0):
        ''' Compute the results for the unfolded lines by taking care about the line order and the group by filter.

        Suppose the line has '-sum' as formulas with 'partner_id' in groupby and 'currency_id' in group by filter.
        The result will be something like:
        [
            (0, 'partner 0', {(0,1): amount1, (0,2): amount2, (1,1): amount3}),
            (1, 'partner 1', {(0,1): amount4, (0,2): amount5, (1,1): amount6}),
            ...               |
        ]    |                |
             |__ res.partner ids
                              |_ key where the first element is the period number, the second one being a res.currency id.

        :param options_list:                The report options list, first one being the current dates range, others
                                            being the comparisons.
        :param calling_financial_report:    The financial report called by the user to be rendered.
        :param sign:                        1 or -1 to get negative values in case of '-sum' formula.
        :return:                            A list (groupby_key, display_name, {key: <balance>...}).
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = [self.groupby] + horizontal_groupby_list
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        groupby_field = self.env['account.move.line']._fields[self.groupby]

        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        analytic_account_id_clause = '''
            AND (
                account_move_line.analytic_account_id = %s OR
                account_move_line.ns_cost_center_id = %s OR
                account_move_line.ns_site_id = %s OR
                account_move_line.ns_project_id = %s OR
                account_move_line.ns_company_id = %s
            )
        ''' % (analytic_account_id, analytic_account_id, analytic_account_id, analytic_account_id, analytic_account_id)
        if analytic_account_id == None:
            analytic_account_id_clause = '''
                AND (
                    account_move_line.analytic_account_id IS NULL AND
                    account_move_line.ns_cost_center_id IS NULL AND
                    account_move_line.ns_site_id IS NULL AND
                    account_move_line.ns_project_id IS NULL AND
                    account_move_line.ns_company_id IS NULL
                )
            '''

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COALESCE(SUM(%s * (account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + ''' AND account_move_line.account_id = ''' + str(parent_groupby_id) + analytic_account_id_clause + ' ' + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params += [i, sign] + where_params

        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}

        parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            results.setdefault(res[self.groupby], {})
            results[res[self.groupby]][key] = res['balance']

        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]


    def _compute_amls_results_real_analytic(self, options_list, calling_financial_report=None, sign=1, parent_groupby_id=0, analytic_account_id=0):
        ''' Compute the results for the unfolded lines by taking care about the line order and the group by filter.

        Suppose the line has '-sum' as formulas with 'partner_id' in groupby and 'currency_id' in group by filter.
        The result will be something like:
        [
            (0, 'partner 0', {(0,1): amount1, (0,2): amount2, (1,1): amount3}),
            (1, 'partner 1', {(0,1): amount4, (0,2): amount5, (1,1): amount6}),
            ...               |
        ]    |                |
             |__ res.partner ids
                              |_ key where the first element is the period number, the second one being a res.currency id.

        :param options_list:                The report options list, first one being the current dates range, others
                                            being the comparisons.
        :param calling_financial_report:    The financial report called by the user to be rendered.
        :param sign:                        1 or -1 to get negative values in case of '-sum' formula.
        :return:                            A list (groupby_key, display_name, {key: <balance>...}).
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = [self.groupby] + horizontal_groupby_list
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        groupby_field = self.env['account.move.line']._fields[self.groupby]

        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        analytic_account_id_clause = '''
            AND (
                account_move_line.analytic_account_id = %s OR
                account_move_line.ns_cost_center_id = %s OR
                account_move_line.ns_site_id = %s OR
                account_move_line.ns_project_id = %s OR
                account_move_line.ns_company_id = %s
            )
        ''' % (analytic_account_id, analytic_account_id, analytic_account_id, analytic_account_id, analytic_account_id)
        if analytic_account_id == None:
            analytic_account_id_clause = '''
                AND (
                    account_move_line.analytic_account_id IS NULL AND
                    account_move_line.ns_cost_center_id IS NULL AND
                    account_move_line.ns_site_id IS NULL AND
                    account_move_line.ns_project_id IS NULL AND
                    account_move_line.ns_company_id IS NULL
                )
            '''

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COALESCE(SUM(%s * (account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + ''' AND account_move_line.account_id = ''' + str(parent_groupby_id) + analytic_account_id_clause + ' ' + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params += [i, sign] + where_params

        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}

        parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            results.setdefault(res[self.groupby], {})
            results[res[self.groupby]][key] = res['balance']

        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]


    def _compute_sum(self, options_list, calling_financial_report=None):        
        self.ensure_one()
        results = super(AccountFinancialReportLine, self)._compute_sum(options_list, calling_financial_report=calling_financial_report)
        results.update({
            'sum_budget': {},
            'sum_if_pos_budget': {},
            'sum_if_pos_groupby_budget': {},
            'sum_if_neg_budget': {},
            'sum_if_neg_groupby_budget': {},
            'sum_real': {},
            'sum_if_pos_real': {},
            'sum_if_pos_groupby_real': {},
            'sum_if_neg_real': {},
            'sum_if_neg_groupby_real': {},
        })

        if options_list[0].get('show_usd_real',False):
            params = []
            queries = []

            AccountFinancialReportHtml = self.financial_report_id
            groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
            all_groupby_list = groupby_list.copy()
            groupby_in_formula = any(x in (self.formulas or '') for x in ('sum_if_pos_groupby', 'sum_if_neg_groupby'))
            if groupby_in_formula and self.groupby and self.groupby not in all_groupby_list:
                all_groupby_list.append(self.groupby)
            groupby_clause = ','.join('account_move_line.%s' % gb for gb in all_groupby_list)

            ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
            parent_financial_report = self._get_financial_report()

            # Prepare a query by period as the date is different for each comparison.

            for i, options in enumerate(options_list):
                new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
                line_domain = self._get_domain(new_options, parent_financial_report)

                tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

                queries.append('''
                    SELECT
                        ''' + (groupby_clause and '%s,' % groupby_clause) + ''' %s AS period_index,
                        COUNT(DISTINCT account_move_line.''' + (self.groupby or 'id') + ''') AS count_rows,
                        COALESCE(SUM(account_move_line.ns_debit_usd_real - account_move_line.ns_credit_usd_real), 0.0) AS balance
                    FROM ''' + tables + '''
                    JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                    WHERE ''' + where_clause + '''
                    ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
                ''')
                params.append(i)
                params += where_params

            
            parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
            for res in self._cr.dictfetchall():
                # Build the key.
                key = [res['period_index']]
                for gb in groupby_list:
                    key.append(res[gb])
                key = tuple(key)

                # Compute values.            
                results['sum_real'][key] = res['balance']
                if results['sum_real'][key] > 0:
                    results['sum_if_pos_real'][key] = results['sum'][key]
                    results['sum_if_pos_groupby_real'].setdefault(key, 0.0)
                    results['sum_if_pos_groupby_real'][key] += res['balance']
                if results['sum_real'][key] < 0:
                    results['sum_if_neg_real'][key] = results['sum'][key]
                    results['sum_if_neg_groupby_real'].setdefault(key, 0.0)
                    results['sum_if_neg_groupby_real'][key] += res['balance']

        if options_list[0].get('show_usd_budget',False):
            params = []
            queries = []

            AccountFinancialReportHtml = self.financial_report_id
            groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
            all_groupby_list = groupby_list.copy()
            groupby_in_formula = any(x in (self.formulas or '') for x in ('sum_if_pos_groupby', 'sum_if_neg_groupby'))
            if groupby_in_formula and self.groupby and self.groupby not in all_groupby_list:
                all_groupby_list.append(self.groupby)
            groupby_clause = ','.join('account_move_line.%s' % gb for gb in all_groupby_list)

            ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
            parent_financial_report = self._get_financial_report()

            # Prepare a query by period as the date is different for each comparison.

            for i, options in enumerate(options_list):
                new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
                line_domain = self._get_domain(new_options, parent_financial_report)

                tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

                queries.append('''
                    SELECT
                        ''' + (groupby_clause and '%s,' % groupby_clause) + ''' %s AS period_index,
                        COUNT(DISTINCT account_move_line.''' + (self.groupby or 'id') + ''') AS count_rows,
                        COALESCE(SUM(account_move_line.ns_debit_usd_budget - account_move_line.ns_credit_usd_budget), 0.0) AS balance
                    FROM ''' + tables + '''
                    JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                    WHERE ''' + where_clause + '''
                    ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
                ''')
                params.append(i)
                params += where_params

            
            parent_financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
            for res in self._cr.dictfetchall():
                # Build the key.
                key = [res['period_index']]
                for gb in groupby_list:
                    key.append(res[gb])
                key = tuple(key)

                # Compute values.            
                results['sum_budget'][key] = res['balance']
                if results['sum_budget'][key] > 0:
                    results['sum_if_pos_budget'][key] = results['sum'][key]
                    results['sum_if_pos_groupby_budget'].setdefault(key, 0.0)
                    results['sum_if_pos_groupby_budget'][key] += res['balance']
                if results['sum_budget'][key] < 0:
                    results['sum_if_neg_budget'][key] = results['sum'][key]
                    results['sum_if_neg_groupby_budget'].setdefault(key, 0.0)
                    results['sum_if_neg_groupby_budget'][key] += res['balance']

        return results
