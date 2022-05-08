# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.osv import expression

from dateutil.relativedelta import relativedelta


class Partner(models.Model):
    _inherit = 'res.partner'

    def get_is_accountant(self):
        self.user_has_groups('account.group_account_user')

    company_type = fields.Selection(selection_add=[('subcompany', 'Subcompany')])
    nrs_company_type = fields.Selection(selection=[('person', 'Individual'), ('subcompany', 'Subcompany'), ('company', 'Company')], string='Company Type', default='person')
    ns_finance_approved = fields.Boolean(string='Finance Approved', default=False, tracking=True)
    ns_is_accountant = fields.Boolean(string='Is Accountant', default=get_is_accountant, compute='_compute_is_accountant')

    # DE44 Dev 1 - Aged Receivable 90days
    ns_usd_currency_id = fields.Many2one('res.currency', string='Currency',
                                         default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    ns_overdue_90 = fields.Monetary(string='Overdue 90 Days', compute='_compute_aged_receivable_90', currency_field="ns_usd_currency_id")

    # DE44 Dev 2 -  Credit Limit
    ns_credit_limit_mrc = fields.Monetary(string='Credit Limit MRC')
    ns_credit_limit_nrc = fields.Monetary(string='Credit Limit NRC')
    ns_fortune_500 = fields.Boolean(string='Fortune 500 Companies')
    ns_sd_approval = fields.Binary(string='Sales Director Approval')

    
    def _compute_is_accountant(self):
        for rec in self:
            rec.ns_is_accountant = self.user_has_groups('account.group_account_user')

    @api.depends('is_company','nrs_company_type')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = partner.nrs_company_type

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.nrs_company_type in ('company','subcompany')

    @api.onchange('company_type','nrs_company_type','type')
    def onchange_company_type(self):
        self.is_company = self.nrs_company_type in ('company','subcompany')

    @api.onchange('type')
    def update_child_company_type(self):
        if self.parent_id:
            if self.type == 'contact':
                self.nrs_company_type = 'person'
            else:
                self.nrs_company_type = 'subcompany'

    def _compute_aged_receivable_90(self):
        today = fields.Date.context_today(self)
        for record in self:
            total_due_90 = 0
            for aml in record.unreconciled_aml_ids:
                if aml.company_currency_id.id != aml.ns_usd_currency_id.id:
                    currency_rates = self.env['crm.fx.rate'].sudo().search(
                        [('currency_id', '=', aml.company_currency_id.id), ('date_start', '<=', aml.date),
                         ('date_end', '>=', aml.date)], limit=1)

                    if not currency_rates:
                        currency_rates = self.env['crm.fx.rate'].sudo().search(
                            [('currency_id', '=', aml.company_currency_id.id)], order='id DESC', limit=1)

                    is_overdue = today > (
                                aml.date_maturity + relativedelta(days=90)) if aml.date_maturity else today > (
                                aml.date + relativedelta(days=90))
                    if currency_rates:
                        amount = aml.amount_residual / currency_rates.rate
                    else:
                        amount = aml.amount_residual

                    if is_overdue and not aml.blocked:
                        total_due_90 += amount
            record.ns_overdue_90 = total_due_90

    @api.model
    def create(self, vals):
        vals['customer_rank'] = 0
        vals['supplier_rank'] = 0        

        res = super(Partner, self).create(vals)
        if res.nrs_company_type == 'person':
            res.is_company = False

        return res


    def write(self, vals):
        if 'ns_from_ui' in self._context and len(self) > 0 and self[0].ns_finance_approved and 'active' not in vals and not self.user_has_groups('account.group_account_user'):
            raise exceptions.UserError(_("You cannot modify Company that has been approved by Finance, please ask your country's Finance Manager to modify"))

        if vals.get('active') is False:
            if 'from_portal' not in self._context and not self.user_has_groups('account.group_account_manager'):
                raise exceptions.UserError(_('Only Accounting/Advisor can archive this record.'))

        return super(Partner, self).write(vals)


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'show_user_partner' not in self._context:
            new_domain = [('partner_share','=',True)]
            domain = expression.AND([new_domain,domain])

        return super(Partner, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if 'show_user_partner' not in self._context:
            new_domain = [('partner_share','=',True)]
            args = expression.AND([new_domain,args])

        return super(Partner, self).name_search(name=name, args=args, operator=operator, limit=limit)


    # def unlink(self):
    #     raise exceptions.UserError("Sorry, you can not delete this record")
