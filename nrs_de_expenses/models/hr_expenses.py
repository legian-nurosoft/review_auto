from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero, float_repr
from odoo.tools.misc import clean_context, format_date
from datetime import date


class HrExpensesStages(models.Model):
    _name = 'hr.expenses.stages'
    _description = "Expenses Stages"

    name = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', copy=False, index=True, help="Status of the expense.")

    email_template = fields.Many2one(comodel_name='mail.template', string='Email Template')


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def action_move_create(self):
        move_group_by_sheet = self._get_account_move_by_sheet()
        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            move = move_group_by_sheet[expense.sheet_id.id]

            move_line_values = move_line_values_by_expense.get(expense.id)

            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        return move_group_by_sheet

    def action_move_post(self):
        move_group_by_sheet = {}

        for expense in self:
            if expense.sheet_id.id not in move_group_by_sheet:
                move = self.sheet_id.account_move_id
                move_group_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_group_by_sheet[expense.sheet_id.id]

        for move in move_group_by_sheet.values():
            move._post()
            move.date = date.today()

        return move_group_by_sheet

    def refuse_expense(self, reason):
        """replace function context to avoid recursive disable send email"""
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        context = self.env.context
        if 'from_refuse_sheet' not in context:
            if self.sheet_id.account_move_id is not False:
                self.sheet_id.account_move_id.with_context(from_refuse_sheet=True).button_cancel()


class HrExpensesSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    ns_expense_sheet_state_helper = fields.Selection([
        ('1_draft', 'Draft'),
        ('2_submit', 'Submitted'),
        ('3_approve', 'Approved'),
        ('4_post', 'Posted'),
        ('5_done', 'Paid'),
        ('6_cancel', 'Refused')
    ], index=True, compute='_compute_state_helper', inverse='_inverse_set_state', store=True)

    @api.depends('state')
    def _compute_state_helper(self):
        for rec in self:
            if rec.state == 'draft':
                rec.ns_expense_sheet_state_helper = '1_draft'
            elif rec.state == 'submit':
                rec.ns_expense_sheet_state_helper = '2_submit'
            elif rec.state == 'approve':
                rec.ns_expense_sheet_state_helper = '3_approve'
            elif rec.state == 'post':
                rec.ns_expense_sheet_state_helper = '4_post'
            elif rec.state == 'done':
                rec.ns_expense_sheet_state_helper = '5_done'
            elif rec.state == 'cancel':
                rec.ns_expense_sheet_state_helper = '6_cancel'

    def _inverse_set_state(self):
        for rec in self:
            if rec.ns_expense_sheet_state_helper == '1_draft':
                if rec.state == 'post':
                    raise UserError(_("You cannot move back expense report that's already posted."))
                elif rec.state == 'done':
                    raise UserError(_("You cannot move back expense report that's already paid."))
                elif rec.state == 'approve':
                    raise UserError(_("You can only post the journal entries or refuse the approved expense report."))
                else:
                    rec.reset_expense_sheets()
            elif rec.ns_expense_sheet_state_helper == '2_submit':
                if rec.state == 'post':
                    raise UserError(_("You cannot move back expense report that's already posted."))
                elif rec.state == 'done':
                    raise UserError(_("You cannot move back expense report that's already paid."))
                elif rec.state == 'cancel':
                    raise UserError(_("You can only move refused expense report to draft."))
                elif rec.state == 'approve':
                    raise UserError(_("You can only post the journal entries or refuse the approved expense report."))
                else:
                    rec.action_submit_sheet()
            elif rec.ns_expense_sheet_state_helper == '3_approve':
                if rec.state == 'post':
                    raise UserError(_("You cannot move back expense report that's already posted."))
                elif rec.state == 'done':
                    raise UserError(_("You cannot move back expense report that's already paid."))
                elif rec.state == 'cancel':
                    raise UserError(_("You can only move refused expense report to draft."))
                elif rec.state == 'draft':
                    raise UserError(_("Please submit the expense report first."))
                else:
                    rec.approve_expense_sheets()
            elif rec.ns_expense_sheet_state_helper == '4_post':
                if rec.state == 'done':
                    raise UserError(_("You cannot move back expense report that's already paid."))
                else:
                    raise UserError(_("Please process journal posting from the expense form."))
            elif rec.ns_expense_sheet_state_helper == '5_done':
                raise UserError(_("Please process payment register from the expense form."))
            elif rec.ns_expense_sheet_state_helper == '6_cancel':
                if rec.state == 'post':
                    raise UserError(_("You cannot refuse expense report that's already posted."))
                elif rec.state == 'done':
                    raise UserError(_("You cannot refuse expense report that's already paid."))
                else:
                    raise UserError(_("Please fill in the reason from the expense form."))

    def write(self, values):
        if 'state' in values:
            state_object = None
            if values['state']:
                if values['state'] == 'submit':
                    state_object = self.env['hr.expenses.stages'].search([('name', '=', 'submit')])
                if values['state'] == 'approve':
                    state_object = self.env['hr.expenses.stages'].search([('name', '=', 'approve')])
                if values['state'] == 'post':
                    state_object = self.env['hr.expenses.stages'].search([('name', '=', 'post')])
                if values['state'] == 'done':
                    state_object = self.env['hr.expenses.stages'].search([('name', '=', 'done')])
                if values['state'] == 'cancel':
                    state_object = self.env['hr.expenses.stages'].search([('name', '=', 'cancel')])
            if state_object:
                filtered_state = state_object.filtered(lambda l:l.email_template.ns_company_id == self.company_id)
                if filtered_state:
                    if filtered_state[0].email_template:
                        email_temp = filtered_state[0].email_template
                        email_temp.send_mail(self.id)
                else:
                    email_temp = state_object[0].email_template
                    email_temp.send_mail(self.id)
        return super(HrExpensesSheet, self).write(values)


    # Approve
    def approve_expense_sheets(self):
        super(HrExpensesSheet, self).approve_expense_sheets()

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Specify expense journal in tab Other Info to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.with_context(clean_context(self.env.context)).action_move_create()

        return res


    # Post Journal Entries
    def action_sheet_move_create(self):
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            if samples.count(False):
                raise UserError(_("You can't mix sample expenses and regular ones"))
            self.write({'state': 'post'})
            return

        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Specify expense journal in tab Other Info to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.with_context(clean_context(self.env.context)).action_move_post()
        for sheet in self.filtered(lambda s: not s.accounting_date):
            sheet.accounting_date = sheet.account_move_id.date
        to_post = self.filtered(lambda sheet: sheet.payment_mode == 'own_account' and sheet.expense_line_ids)
        to_post.write({'state': 'post'})
        (self - to_post).write({'state': 'done'})
        self.activity_update()
        return res

    @api.model
    def _default_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', default_company_id), ('ns_expenses_journal', '=', True)], limit=1)
        return journal

    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=True, domain="[('type', '=', 'purchase'), ('company_id', '=', company_id), ('ns_expenses_journal', '=', True)]",
        default=_default_journal_id, help="The journal used when the expense is done.")

    #Refuse
    def refuse_sheet(self, reason):
        """replace to disable email sent and add context to avoid recursive"""
        if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot refuse your own expenses"))

            if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
                raise UserError(_("You can only refuse your department expenses"))

        self.write({'state': 'cancel'})
        if self.account_move_id is not False:
            self.account_move_id.with_context(from_refuse_sheet=True).button_cancel()  
    
    def activity_update(self):
        """do nothing on activity update"""
        pass
    
    