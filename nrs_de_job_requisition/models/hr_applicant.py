# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from datetime import date

class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    ns_approved_by_finance_manager = fields.Boolean(default=False)
    ns_approved_by_human_resource_manager = fields.Boolean(default=False)
    ns_approved_by_ceo_office_manager = fields.Boolean(default=False)
    ns_approved = fields.Boolean(default=False)

    ns_show_finance_approval_button = fields.Boolean(compute='_compute_ns_show_finance_approval_button')
    ns_show_human_resource_approval_button = fields.Boolean(compute='_compute_ns_show_human_resource_approval_button')
    ns_show_ceo_office_approval_button = fields.Boolean(compute='_compute_ns_show_ceo_office_approval_button')
    ns_show_approval_button = fields.Boolean(compute='_compute_ns_show_approval_button')

    ns_name_local_language = fields.Char("Name (local language if applicable)")
    ns_preferred_title = fields.Selection(selection=[('mr', "Mr"), ('mrs', "Mrs"), ('ms', "Ms"), ('other', "Other")], string="Preferred Title")
    ns_other_preferred_title = fields.Char("Other Preferred Title")

    ns_home_address = fields.Char("Home Address")
    ns_visa_required = fields.Selection(selection=[('yes', "Yes"), ('no', "No")], string="Visa Sponsorship Required")
    ns_tentative_start_date = fields.Date("Tentative Start Date")
    ns_job_requisition_id = fields.Many2one(related="job_id.ns_job_requisition_id")
    ns_hiring_manager = fields.Many2one(related="ns_job_requisition_id.ns_user_id")
    ns_hiring_managers_manager = fields.Many2one(related="ns_job_requisition_id.ns_hiring_managers_manager")
    ns_application_source = fields.Selection(selection=[('direct', "Direct Application"), ('referral', "Referral"), ('agency', "Agency")], string="Application Source")
    ns_name_of_employee_referrer = fields.Char("Name of Employee Referrer (if applicable)")
    ns_external_agency_name = fields.Char("External Agency Name (if applicable)")
    ns_interview_panel_names = fields.Char("Interview Panel Names")
    ns_reference_check_date = fields.Date("External Reference Checks Completion Date")
    ns_reason_for_no_external_reference_check = fields.Char("Reason for no External Reference Check")
    ns_background_check_requirement = fields.Selection(selection=[('yes', "Yes"), ('no', "No")], string="Background Check Requirement")
    ns_reason_for_no_background_check = fields.Char("Reason for no Background Check")

    department_id = fields.Many2one(related="job_id.department_id", readonly=True)
    ns_hire_group = fields.Selection(related="ns_job_requisition_id.ns_hire_group")
    ns_project_name = fields.Char(related="ns_job_requisition_id.ns_project_name")
    ns_work_location = fields.Selection(related="ns_job_requisition_id.ns_work_location")
    ns_business_justification_for_hire = fields.Text(related="ns_job_requisition_id.ns_business_justification_for_hire")
    ns_proposed_job_title = fields.Char(related="ns_job_requisition_id.ns_role_job_title")
    ns_reporting_manager = fields.Char("Reporting Manager")
    ns_dotted_line_manager = fields.Char("Dotted Line Manager (if applicable)")

    ns_name_of_employer = fields.Char("Name of Employer")
    ns_annual_salary = fields.Char("Annual Salary")
    ns_bonus = fields.Char("Bonus")
    ns_other_payments_allowances = fields.Char("Other payments/allowances")
    ns_method_of_verifying_compensation_details = fields.Char("Method of verifying compensation details")
    ns_non_compete_non_solicitation_period = fields.Char("Non-compete/non-solicitation period")

    ns_headcount_approved = fields.Selection(selection=[('budgeted', "Budgeted headcount"), ('new', "New headcount")], string="Headcount Approved")
    ns_type_of_incentive_plan = fields.Selection(selection=[('annual', "Annual Bonus Plan (ABP)"), ('sales', "Sales Incentive Plan (SIP)")], string="Type of Incentive Plan")
    ns_currency_id = fields.Many2one('res.currency', "Currency")
    ns_annual_base_salary = fields.Monetary("Annual Base Salary", currency_field="ns_currency_id")
    ns_annual_bonus_amount = fields.Monetary("Annual Bonus Amount", currency_field="ns_currency_id")
    ns_percent_of_base_salary = fields.Float("% of base salary")
    ns_sales_commission_amount = fields.Monetary("Sales Commission Amount", currency_field="ns_currency_id")
    ns_pay_mix_split = fields.Char("Pay Mix Split")
    ns_total_target_compensation_ttc = fields.Monetary("Total Target Compensation (TTC)", currency_field="ns_currency_id")
    ns_total_target_compensation_ttc_commision = fields.Monetary(string="Total Target Compensation (TTC)(Commision)", currency_field="ns_currency_id")
    ns_diff_between_budgeted_vs_proposed_ttc = fields.Monetary("Diff. between budgeted vs proposed TTC", currency_field="ns_currency_id")
    ns_diff_between_budgeted_vs_proposed_ttc_commision = fields.Monetary("Diff. between budgeted vs proposed TTC(Commision)", currency_field="ns_currency_id")

    ns_usd_currency_id = fields.Many2one('res.currency', "USD Currency", default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]), readonly=True)
    ns_annual_base_salary_usd = fields.Monetary("Annual Base Salary (USD)", currency_field="ns_usd_currency_id", compute='_compute_proposed_compensation_usd', store=True)
    ns_annual_bonus_amount_usd = fields.Monetary("Annual Bonus Amount (USD)", currency_field="ns_usd_currency_id", compute='_compute_proposed_compensation_usd', store=True)
    ns_sales_commission_amount_usd = fields.Monetary("Sales Commission Amount (USD)", currency_field="ns_usd_currency_id", compute='_compute_proposed_compensation_usd', store=True)
    ns_total_target_compensation_ttc_usd = fields.Monetary("Total Target Compensation (TTC) (USD)", currency_field="ns_usd_currency_id", compute='_compute_proposed_compensation_usd', store=True)
    ns_diff_between_budgeted_vs_proposed_ttc_usd = fields.Monetary("Diff. between budgeted vs proposed TTC (USD)", currency_field="ns_usd_currency_id", compute='_compute_proposed_compensation_usd', store=True)

    ns_additional_one_time_payment = fields.Monetary("Additional one-time payment", currency_field="ns_hr_currency_id")
    ns_hr_currency_id = fields.Many2one('res.currency', "Currency")
    ns_additional_one_time_payment_usd = fields.Monetary("Additional one-time payment (USD)", currency_field="ns_usd_currency_id", compute='_compute_hr_usd', store=True)
    ns_grade = fields.Selection(selection=[
        ('x1-a', "X1-A"), 
        ('x1-b', "X1-B"), 
        ('x1-c', "X1-C"), 
        ('x2-a', "X2-A"), 
        ('x2-b', "X2-B"), 
        ('x2-c', "X2-C"), 
        ('e1', "E1"), 
        ('e2', "E2"), 
        ('e3', "E3"), 
        ('e4', "E4"), 
        ('e5', "E5"), 
        ('a1', "A1"), 
        ('a2', "A2"), 
        ('a3', "A3")], string="Grade")
    ns_carry_points = fields.Char("Carry Points")
    ns_headcount_plan_budget_ttc = fields.Monetary(related="ns_job_requisition_id.ns_total_target_compensation_ttc", string="Headcount Plan Budget(TTC)", currency_field="ns_currency_id")
    ns_headcount_plan_budget_ttc_commision = fields.Monetary(related="ns_job_requisition_id.ns_total_target_compensation_ttc_commision", string="Headcount Plan Budget(TTC)(Commision)", currency_field="ns_currency_id")


    @api.onchange('ns_headcount_plan_budget_ttc', 'ns_total_target_compensation_ttc')
    def calculate_ns_diff_between_budgeted_vs_proposed_ttc(self):
        self.ns_diff_between_budgeted_vs_proposed_ttc = self.ns_headcount_plan_budget_ttc - self.ns_total_target_compensation_ttc
    
    @api.onchange('ns_headcount_plan_budget_ttc_commision', 'ns_total_target_compensation_ttc_commision')
    def calculate_ns_diff_between_budgeted_vs_proposed_ttc_commision(self):
        self.ns_diff_between_budgeted_vs_proposed_ttc_commision = self.ns_headcount_plan_budget_ttc_commision - self.ns_total_target_compensation_ttc_commision
        
    @api.depends('ns_currency_id', 'ns_annual_base_salary', 'ns_annual_bonus_amount', 'ns_sales_commission_amount', 'ns_total_target_compensation_ttc', 'ns_diff_between_budgeted_vs_proposed_ttc')
    def _compute_proposed_compensation_usd(self):
        for rec in self:
            #depend crm.fx.rate
            if rec.create_date:
                record_date = rec.create_date.strftime('%Y-%m-%d')
            else:
                record_date = date.today().strftime('%Y-%m-%d')
            fx_rate = self.env["crm.fx.rate"].search([('currency_id', '=', rec.ns_currency_id.id), ('date_start', '<=', record_date), ('date_end', '>=', record_date)])
            if fx_rate:
                rec.ns_annual_base_salary_usd = rec.ns_annual_base_salary / fx_rate.rate if fx_rate.rate else 0.0
                rec.ns_annual_bonus_amount_usd = rec.ns_annual_bonus_amount / fx_rate.rate if fx_rate.rate else 0.0
                rec.ns_sales_commission_amount_usd = rec.ns_sales_commission_amount / fx_rate.rate if fx_rate.rate else 0.0
                rec.ns_total_target_compensation_ttc_usd = rec.ns_total_target_compensation_ttc / fx_rate.rate if fx_rate.rate else 0.0
                rec.ns_diff_between_budgeted_vs_proposed_ttc_usd = rec.ns_diff_between_budgeted_vs_proposed_ttc / fx_rate.rate if fx_rate.rate else 0.0
            else:
                rec.ns_annual_base_salary_usd = 0.0
                rec.ns_annual_bonus_amount_usd = 0.0
                rec.ns_sales_commission_amount_usd = 0.0
                rec.ns_total_target_compensation_ttc_usd = 0.0
                rec.ns_diff_between_budgeted_vs_proposed_ttc_usd = 0.0

    @api.depends('ns_hr_currency_id', 'ns_additional_one_time_payment')
    def _compute_hr_usd(self):
        for rec in self:
            #depend crm.fx.rate
            if rec.create_date:
                record_date = rec.create_date.strftime('%Y-%m-%d')
            else:
                record_date = date.today().strftime('%Y-%m-%d')
            fx_rate = self.env["crm.fx.rate"].search([('currency_id', '=', rec.ns_hr_currency_id.id), ('date_start', '<=', record_date ), ('date_end', '>=', record_date)])
            if fx_rate:
                rec.ns_additional_one_time_payment_usd = rec.ns_additional_one_time_payment / fx_rate.rate if fx_rate.rate else 0.0
            else:
                rec.ns_additional_one_time_payment_usd = 0.00

    def _compute_ns_show_finance_approval_button(self):
        for rec in self:
            show = False
            stage = rec.stage_id
            company = rec.company_id
            if stage.ns_need_approval_from_manager and not rec.ns_approved_by_finance_manager:
                finance_manager = self.env['hr.department'].search(
                    [('name','=','Finance'), ('company_id','=',company.id),
                     ('manager_id.user_id', '=', self.env.user.id)])
                if finance_manager:
                    show = True
            rec.ns_show_finance_approval_button = show

    def _compute_ns_show_human_resource_approval_button(self):
        for rec in self:
            show = False
            stage = rec.stage_id
            company = rec.company_id
            if stage.ns_need_approval_from_manager and not rec.ns_approved_by_human_resource_manager:
                hr_manager = self.env['hr.department'].search(
                    [('name', '=', 'Human Resources'), ('company_id', '=', company.id),
                     ('manager_id.user_id', '=', self.env.user.id)])
                if hr_manager:
                    show = True
            rec.ns_show_human_resource_approval_button = show

    def _compute_ns_show_ceo_office_approval_button(self):
        for rec in self:
            show = False
            stage = rec.stage_id
            company = rec.company_id
            if stage.ns_need_approval_from_manager and not rec.ns_approved_by_ceo_office_manager:
                ceo_manager = self.env['hr.department'].search(
                    [('name', '=', 'CEO Office'), ('company_id', '=', company.id),
                     ('manager_id.user_id', '=', self.env.user.id)])
                if ceo_manager:
                    show = True
            rec.ns_show_ceo_office_approval_button = show

    def _compute_ns_show_approval_button(self):
        for rec in self:
            show = False
            stage = rec.stage_id
            company = rec.company_id
            if stage.ns_need_approval_from_manager and not rec.ns_approved:
                show = True
            rec.ns_show_approval_button = show

    def move_to_approval_stage(self):
        if self.ns_approved_by_finance_manager and self.ns_approved_by_human_resource_manager and self.ns_approved_by_ceo_office_manager:
            stage_id = self.env['hr.recruitment.stage'].search([(('ns_approval_stage','=',True))],limit=1)
            if stage_id:
                self.write({'stage_id': stage_id.id})

    def move_to_approval_stage_gen(self):
        if self.ns_approved:
            stage_id = self.env['hr.recruitment.stage'].search([(('ns_approval_stage','=',True))],limit=1)
            if stage_id:
                self.write({'stage_id': stage_id.id})

    def do_approval_by_finance_manager(self):
        self.write({'ns_approved_by_finance_manager': True})
        self.message_post(body="Approved by Finance Manager")
        self.move_to_approval_stage()

    def do_approval_by_human_resource_manager(self):
        self.write({'ns_approved_by_human_resource_manager': True})
        self.message_post(body="Approved by Human Resource Manager")
        self.move_to_approval_stage()

    def do_approval_by_ceo_office_manager(self):
        self.write({'ns_approved_by_ceo_office_manager': True})
        self.message_post(body="Approved by CEO Office Manager")
        self.move_to_approval_stage()

    def do_approval(self):
        self.write({'ns_approved': True})
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])[0]
        self.message_post(body=_("Approved by %s", user_id.name))
        self.move_to_approval_stage_gen()

    def archive_applicant(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Decline Reason'),
            'res_model': 'applicant.get.refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_applicant_ids': self.ids, 'active_test': False},
            'views': [[False, 'form']]
        }

    def write(self, vals):
        if vals.get('stage_id',False):
            stage_id = self.env['hr.recruitment.stage'].browse(vals.get('stage_id',False))
            if stage_id and stage_id.ns_approval_stage:
                if not self.ns_approved:
                    raise exceptions.ValidationError(_('This applicant is not yet approved, please check your approval requirement.'))

        return super(HRApplicant, self).write(vals)

class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'
    _description = 'Get Decline Reason'

    refuse_reason_id = fields.Many2one('hr.applicant.refuse.reason', 'Decline Reason')
