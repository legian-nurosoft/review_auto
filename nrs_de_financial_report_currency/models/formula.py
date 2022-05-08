# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.account_reports.models.formula import FormulaLocals, FormulaSolver

from odoo.tools.safe_eval import safe_eval
import re
import ast


def __getitem__(self, item):
    if item in ('NDays', 'NDays_budget', 'NDays_real'):
        return self.solver._get_number_of_days(self.key[0])
    elif item == 'from_context':
        return self.solver._get_balance_from_context(self.financial_line)
    elif item == 'count_rows':
        return self.solver._get_amls_results(self.financial_line)[item].get(self.key[0], 0)
    elif item in ('sum', 'sum_if_pos', 'sum_if_neg', 'sum_if_pos_groupby', 'sum_if_neg_groupby'):
        return self.solver._get_amls_results(self.financial_line)[item].get(self.key, 0.0)
    elif item in ('sum_budget', 'sum_if_pos_budget', 'sum_if_neg_budget', 'sum_if_pos_groupby_budget', 'sum_if_neg_groupby_budget'):
        return self.solver._get_amls_results(self.financial_line)[item].get(self.key, 0.0)
    elif item in ('sum_real', 'sum_if_pos_real', 'sum_if_neg_real', 'sum_if_pos_groupby_real', 'sum_if_neg_groupby_real'):
        return self.solver._get_amls_results(self.financial_line)[item].get(self.key, 0.0)
    else:
        if '_budget' in item:
            financial_line = self.solver._get_line_by_code(item.replace('_budget',''))
            if not financial_line:
                return super().__getitem__(item)
            return self.solver._get_formula_results_budget(financial_line).get(self.key, 0.0)
        elif '_real' in item:
            financial_line = self.solver._get_line_by_code(item.replace('_real',''))
            if not financial_line:
                return super().__getitem__(item)
            return self.solver._get_formula_results_real(financial_line).get(self.key, 0.0)
        else:
            financial_line = self.solver._get_line_by_code(item)
            if not financial_line:
                return super().__getitem__(item)
            return self.solver._get_formula_results(financial_line).get(self.key, 0.0)

FormulaLocals.__getitem__ = __getitem__


def get_results_budget(self, financial_line):
        ''' Get results for the given financial report line.
        :param financial_line:  A record of the account.financial.html.report.line model.
        :return: see 'cache_results_by_id' for more details.
        '''
        if financial_line.id not in self.cache_results_by_id:
            # The financial line has not pre-computed using '_prefetch_line'. Then, it could lead to some
            # wrong values.
            return {}

        # Ensure values are computed. This part is done lazily.
        self._get_formula_results_budget(financial_line)

        return self.cache_results_by_id[financial_line.id]

def _get_formula_results_budget(self, financial_line):
        ''' Get or compute the 'formula' results of a financial report line (see 'cache_results_by_id').
        :param financial_line:  A record of the account.financial.html.report.line model.
        :return: see 'cache_results_by_id', 'formula' key.
        '''
        self.cache_results_by_id.setdefault(financial_line.id, {})

        if 'formula_budget' not in self.cache_results_by_id[financial_line.id]:
            results = {}
            if financial_line.formulas:
                for key in self.encountered_keys:
                    # Compute formula for each key.
                    results[key] = self._eval_formula_budget(financial_line, key)

            self.cache_results_by_id[financial_line.id]['formula_budget'] = results

        return self.cache_results_by_id[financial_line.id]['formula_budget']

def _eval_formula_budget(self, financial_line, key):
        ''' Evaluate the current formula using the custom object passed as parameter as locals.
        :param financial_line:  A record of the account.financial.html.report.line model.
        :param key:             A tuple being the concatenation of the period index plus the additional group-by keys.
                                Suppose you are evaluating the formula for 'partner_id'=3 for the first comparison, the
                                key will be (1, 3).
        '''
        if not financial_line.formulas:
            return 0.0

        try:
            formulas = financial_line.formulas.split(" ")
            for i in range(len(formulas)):
                if formulas[i].strip() not in ['-', '+', '/', '*', '%']:
                    formulas[i] = formulas[i].strip() + '_budget'
            budget_formulas = " ".join(formulas)
            return safe_eval(budget_formulas, globals_dict=FormulaLocals(self, financial_line, key), nocopy=True)
        except ZeroDivisionError:
            return 0.0


def get_results_real(self, financial_line):
        ''' Get results for the given financial report line.
        :param financial_line:  A record of the account.financial.html.report.line model.
        :return: see 'cache_results_by_id' for more details.
        '''
        if financial_line.id not in self.cache_results_by_id:
            # The financial line has not pre-computed using '_prefetch_line'. Then, it could lead to some
            # wrong values.
            return {}

        # Ensure values are computed. This part is done lazily.
        self._get_formula_results_real(financial_line)

        return self.cache_results_by_id[financial_line.id]

def _get_formula_results_real(self, financial_line):
        ''' Get or compute the 'formula' results of a financial report line (see 'cache_results_by_id').
        :param financial_line:  A record of the account.financial.html.report.line model.
        :return: see 'cache_results_by_id', 'formula' key.
        '''
        self.cache_results_by_id.setdefault(financial_line.id, {})

        if 'formula_real' not in self.cache_results_by_id[financial_line.id]:
            results = {}
            if financial_line.formulas:
                for key in self.encountered_keys:
                    # Compute formula for each key.
                    results[key] = self._eval_formula_real(financial_line, key)

            self.cache_results_by_id[financial_line.id]['formula_real'] = results

        return self.cache_results_by_id[financial_line.id]['formula_real']

def _eval_formula_real(self, financial_line, key):
        ''' Evaluate the current formula using the custom object passed as parameter as locals.
        :param financial_line:  A record of the account.financial.html.report.line model.
        :param key:             A tuple being the concatenation of the period index plus the additional group-by keys.
                                Suppose you are evaluating the formula for 'partner_id'=3 for the first comparison, the
                                key will be (1, 3).
        '''
        if not financial_line.formulas:
            return 0.0

        try:
            formulas = financial_line.formulas.split(" ")
            for i in range(len(formulas)):
                if formulas[i].strip() not in ['-', '+', '/', '*', '%']:
                    formulas[i] = formulas[i].strip() + '_real'
            real_formulas = " ".join(formulas)
            return safe_eval(real_formulas, globals_dict=FormulaLocals(self, financial_line, key), nocopy=True)
        except ZeroDivisionError:
            return 0.0


FormulaSolver.get_results_budget = get_results_budget
FormulaSolver._get_formula_results_budget = _get_formula_results_budget
FormulaSolver._eval_formula_budget = _eval_formula_budget

FormulaSolver.get_results_real = get_results_real
FormulaSolver._get_formula_results_real = _get_formula_results_real
FormulaSolver._eval_formula_real = _eval_formula_real