# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _
import datetime
from dateutil.relativedelta import relativedelta 
    
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_ns_can_edit_restricted_field(self):
        return self.user_has_groups('hr.group_hr_manager')

    # change the field access right
    address_home_id = fields.Many2one(groups='base.group_user')
    barcode = fields.Char(groups='base.group_user')
    birthday = fields.Date(groups='base.group_user')
    certificate = fields.Selection(groups='base.group_user')
    children = fields.Integer(groups='base.group_user')
    country_of_birth = fields.Many2one(groups='base.group_user')
    emergency_contact = fields.Char(groups='base.group_user')
    emergency_phone = fields.Char(groups='base.group_user')
    bank_account_id = fields.Many2one('res.partner.bank', groups='base.group_user')
    country_id = fields.Many2one(groups='base.group_user')
    phone = fields.Char(groups='base.group_user')
    gender = fields.Selection(groups='base.group_user')
    identification_id = fields.Char(groups='base.group_user')
    km_home_work = fields.Integer(groups='base.group_user')
    marital = fields.Selection(groups='base.group_user')
    passport_id = fields.Char(groups='base.group_user')
    permit_no = fields.Char(groups='base.group_user')
    pin = fields.Char(groups='base.group_user')
    place_of_birth = fields.Char(groups='base.group_user')
    spouse_birthdate = fields.Date(groups='base.group_user')
    spouse_complete_name = fields.Char(groups='base.group_user')
    study_field = fields.Char(groups='base.group_user')
    study_school = fields.Char(groups='base.group_user')
    visa_expire = fields.Date(groups='base.group_user')
    visa_no = fields.Char(groups='base.group_user')

    ns_surename = fields.Char(string="Surname")
    ns_first_name = fields.Char(string="First Name")
    ns_middle_name = fields.Char(string="Middle Name")
    ns_english_name = fields.Char(string="Preferred English Name")
    ns_prefix = fields.Selection([('mr', 'Mr.'), ('mrs', 'Mrs.'), ('miss', 'Ms.'), ('other', 'Other')], 'Prefix')
    ns_employee_id = fields.Char(string="Employee ID")
    ns_cost_center_id = fields.Many2one('account.analytic.account', string='Department Cost Centre')
    ns_job_title = fields.Many2one('hr.job.position', string='Job Title')
    ns_head_of_department = fields.Many2one('res.users', string='Head of Department')
    ns_head_of_group = fields.Many2one('res.users', string='Head of Group (Executive Leadership Team)')
    ns_employee_type = fields.Selection([('employee', 'Employee'), ('contractor', 'Contractor')], 'Employee Type')
    ns_working_hours_type = fields.Selection([('flexible', 'Flexible working hours '),
                                              ('calculating', 'Comprehensive calculating work hours')],
                                             string='Working Hours Type', groups="hr.group_hr_manager")
    ns_start_date = fields.Date(string="Start Date")
    ns_end_date = fields.Date(string="End Date")
    ns_years_of_service = fields.Integer(compute="_compute_year_of_service", string='Years of Service', readonly=True)
    ns_home_address = fields.Char(string="Home Address")
    ns_contact_number = fields.Char(string="Contact Number")
    ns_personal_email = fields.Char(string="Personal Email")
    ns_age = fields.Integer(compute="_compute_employee_age", string="Age", readonly=True)
    ns_blood_type = fields.Selection([('blood_a', 'A'), ('blood_b', 'B'), ('blood_ab', 'AB'), ('blood_o', 'O')], 'Blood Type')
    ns_politic_status = fields.Char(string="Politic Status")
    ns_health_status = fields.Selection([('good', 'Good'), ('fair', 'Fair'), ('disease', 'Have Disease')], 'Health Status')
    ns_health_details = fields.Char(string="Health Details")
    ns_hukou_address = fields.Char(string="Hukou Address")
    ns_tax_file_city = fields.Char(string="Tax File City")
    ns_former_employer = fields.Char(string="Former Employer")
    ns_nric_issue_date = fields.Date(string="NRIC Issue Date")
    ns_race = fields.Char(string="Race")
    ns_spouse_gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], 'Spouse Gender')
    ns_spouse_id_no = fields.Char(string="Spouse ID No / Passport No")
    ns_spouse_occupation = fields.Char(string="Spouse Occupation")
    ns_spouse_mobile = fields.Char(string="Spouse Contact Number")
    ns_children = fields.One2many('ns.employees.children', 'employee_id', string='Children')
    ns_contact_relationship = fields.Char(string="Contact Relationship")
    ns_emergency_phone = fields.Char(string="Contact Number")
    ns_emergency_email = fields.Char(string="Contact Email")
    ns_fund_contribution = fields.Selection([('cdac', 'CDAC'), ('ecf', 'ECF'), ('sinda', 'SINDA'), ('mbmf', 'MBMF')], 'Fund Contribution')
    ns_basic_pension_number = fields.Char(string="Basic Pension Number")
    ns_employment_insurance_number = fields.Char(string="Employment Insurance Certificate Number")
    ns_mpf_entitlement = fields.Char(string="MPF Entitlement")
    ns_mpf_exempted_reason = fields.Char(string="MPF Exempted Reason")
    ns_insurance = fields.Char(string="Insurance")
    ns_healthcare = fields.Char(string="Healthcare")
    #X1-A, X1-B, X1-C, X2-A, X2-B, X2-C, E1, E2, E3, E4, E5, A1, A2, A3
    ns_grade = fields.Selection([('grade_x1a','X1-A'), ('grade_x1b','X1-B'), ('grade_x1c','X1-C'),
                                 ('grade_x2a','X2-A'), ('grade_x2b','X2-B'), ('grade_x2c','X2-C'),
                                 ('grade_e1', 'E1'), ('grade_e2', 'E2'), ('grade_e3', 'E3'), ('grade_e4', 'E4'),
                                 ('grade-e5', 'E5'), ('grade_ex1', 'EX-1'), ('grade_a1', 'A1'), ('grade_a2', 'A2'),
                                 ('grade_a3', 'A3')], 'Grade')
    ns_currency_id = fields.Many2one('res.currency', string='Currency')
    ns_commuting_cost = fields.Float(string="Commuting Cost")
    ns_annual_base_salary = fields.Monetary(string="Annual Base Salary", currency_field="ns_currency_id")
    ns_incentive_plan = fields.Selection([('bonus', 'Annual Bonus Plan'), ('sales', 'Sales Incentive Plan')], 'Incentive Plan')
    ns_annual_bonus_plan = fields.Float(string="Annual Bonus Plan (% of base salary)")
    ns_sales_incentive_plan = fields.Float(string="Sales Incentive Plan (% of base salary)")
    ns_annual_total_target_compensation = fields.Monetary(string='Annual Total Target Compensation', currency_field="ns_currency_id", readonly=True)
    ns_carry_points = fields.Integer(string="Carry Points")
    ns_payroll_number = fields.Char(string="Payroll Number")
    ns_bank_name = fields.Char(string="Name of Bank")
    ns_account_holder = fields.Char(string="Name of Account Holder")
    ns_account_number = fields.Char(string="Account No")
    ns_swift_code = fields.Char(string="SWIFT Code")
    is_show_personal_details = fields.Boolean(compute='_compute_is_show_personal_details', readonly=True)
    ns_company_country = fields.Char(compute='_compute_company_country', string='Country', readonly=True)
    ns_can_edit_restricted_field = fields.Boolean(default=_get_ns_can_edit_restricted_field, compute='_compute_ns_can_edit_restricted_field')

    
    @api.constrains('ns_children','children')
    def _check_children_count(self):
        if not self._context.get('from_my_profile', False):
            for rec in self:
                if rec.children != len(rec.ns_children):
                    raise exceptions.ValidationError(_('The children count is not mathced.'))

    def _compute_ns_can_edit_restricted_field(self):
        for rec in self:
            rec.ns_can_edit_restricted_field = True if rec.user_id.id == self.env.user.id or self.user_has_groups('hr.group_hr_manager') else False

    @api.depends('ns_start_date', 'ns_end_date')
    def _compute_year_of_service(self):
        for emp in self:
            today = datetime.date.today()
            if emp.ns_end_date:
                today = emp.ns_end_date
            yos = abs(relativedelta(today, emp.ns_start_date).years)
            emp.ns_years_of_service = yos

    @api.depends('birthday')
    def _compute_employee_age(self):
        for emp in self:
            today = datetime.date.today()
            emp.ns_age = relativedelta(today, emp.birthday).years

    @api.model
    def _calculate_age_and_work_year(self):
        for emp in self:
            today = datetime.date.today()
            if not emp.ns_end_date:
                emp.ns_years_of_service = abs(relativedelta(today, emp.ns_start_date).years)
            emp.ns_age = relativedelta(today, emp.birthday).years

    @api.depends('address_id')
    def _compute_is_show_personal_details(self):
        for emp in self:
            if 'chuanjun' in emp.address_id.name.lower():
                emp.is_show_personal_details = True
            else :
                emp.is_show_personal_details = False

    @api.depends('company_id')
    def _compute_company_country(self):
        for emp in self:
            emp.ns_company_country = emp.company_id.country_id.name

    @api.onchange('ns_incentive_plan')
    def onchange_incentive_plan(self):
        self.ns_annual_bonus_plan = 0
        self.ns_sales_incentive_plan = 0

    @api.onchange('ns_annual_bonus_plan')
    def _recompute_annual_compensation_bonus(self):
        for emp in self:
            if emp.ns_annual_bonus_plan:
                emp.ns_annual_total_target_compensation = emp.ns_annual_base_salary * (1 + (emp.ns_annual_bonus_plan/100))
            else : emp.ns_annual_total_target_compensation = 0

    @api.onchange('ns_sales_incentive_plan')
    def _recompute_annual_compensation_sales(self):
        for emp in self:
            if emp.ns_sales_incentive_plan:
                emp.ns_annual_total_target_compensation = emp.ns_annual_base_salary * (1 + (emp.ns_sales_incentive_plan / 100))
            else : emp.ns_annual_total_target_compensation = 0

class NsEmployeeChildren(models.Model):
    _name = 'ns.employees.children'

    employee_id = fields.Many2one('hr.employee', string='Parent')
    ns_child_name = fields.Char(string='Complete Name')
    ns_child_id = fields.Char(string='ID No/Passport No')
    ns_child_date_of_birth = fields.Char(string='Date of Birth')
    ns_child_occupation = fields.Char(string='Occupation')

class HrEmployeePublic(models.Model):
    """all new field on hr employee nedd to be added here too to avoid error for non employee user"""
    _inherit = 'hr.employee.public'
    
    ns_surename = fields.Char(string="Surname")
    ns_first_name = fields.Char(string="First Name")
    ns_middle_name = fields.Char(string="Middle Name")
    ns_english_name = fields.Char(string="Preferred English Name")
    ns_prefix = fields.Selection([('mr', 'Mr.'), ('mrs', 'Mrs.'), ('miss', 'Ms.'), ('other', 'Other')], 'Prefix')
    ns_employee_id = fields.Char(string="Employee ID")
    ns_cost_center_id = fields.Many2one('account.analytic.account', string='Department Cost Centre')
    ns_job_title = fields.Many2one('hr.job.position', string='Job Title')
    ns_head_of_department = fields.Many2one('res.users', string='Head of Department')
    ns_head_of_group = fields.Many2one('res.users', string='Head of Group (Executive Leadership Team)')
    ns_employee_type = fields.Selection([('employee', 'Employee'), ('contractor', 'Contractor')], 'Employee Type')
    ns_start_date = fields.Date(string="Start Date")
    ns_end_date = fields.Date(string="End Date")
    ns_years_of_service = fields.Integer(compute="_compute_year_of_service", string='Years of Service', readonly=True)
    ns_home_address = fields.Char(string="Home Address")
    ns_contact_number = fields.Char(string="Contact Number")
    ns_personal_email = fields.Char(string="Personal Email")
    ns_age = fields.Integer(compute="_compute_employee_age", string="Age", readonly=True)
    ns_blood_type = fields.Selection([('blood_a', 'A'), ('blood_b', 'B'), ('blood_ab', 'AB'), ('blood_o', 'O')], 'Blood Type')
    ns_politic_status = fields.Char(string="Politic Status")
    ns_health_status = fields.Selection([('good', 'Good'), ('fair', 'Fair'), ('disease', 'Have Disease')], 'Health Status')
    ns_health_details = fields.Char(string="Health Details")
    ns_hukou_address = fields.Char(string="Hukou Address")
    ns_tax_file_city = fields.Char(string="Tax File City")
    ns_former_employer = fields.Char(string="Former Employer")
    ns_nric_issue_date = fields.Date(string="NRIC Issue Date")
    ns_race = fields.Char(string="Race")
    ns_spouse_gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], 'Spouse Gender')
    ns_spouse_id_no = fields.Char(string="Spouse ID No / Passport No")
    ns_spouse_occupation = fields.Char(string="Spouse Occupation")
    ns_spouse_mobile = fields.Char(string="Spouse Contact Number")
    ns_children = fields.One2many('ns.employees.children', 'employee_id', string='Children')
    ns_contact_relationship = fields.Char(string="Contact Relationship")
    ns_emergency_phone = fields.Char(string="Contact Number")
    ns_emergency_email = fields.Char(string="Contact Email")
    ns_fund_contribution = fields.Selection([('cdac', 'CDAC'), ('ecf', 'ECF'), ('sinda', 'SINDA'), ('mbmf', 'MBMF')], 'Fund Contribution')
    ns_basic_pension_number = fields.Char(string="Basic Pension Number")
    ns_employment_insurance_number = fields.Char(string="Employment Insurance Certificate Number")
    ns_mpf_entitlement = fields.Char(string="MPF Entitlement")
    ns_mpf_exempted_reason = fields.Char(string="MPF Exempted Reason")
    ns_insurance = fields.Char(string="Insurance")
    ns_healthcare = fields.Char(string="Healthcare")
    #X1-A, X1-B, X1-C, X2-A, X2-B, X2-C, E1, E2, E3, E4, E5, A1, A2, A3
    ns_grade = fields.Selection([('grade_x1a','X1-A'), ('grade_x1b','X1-B'), ('grade_x1c','X1-C'),
                                 ('grade_x2a','X2-A'), ('grade_x2b','X2-B'), ('grade_x2c','X2-C'),
                                 ('grade_e1', 'E1'), ('grade_e2', 'E2'), ('grade_e3', 'E3'), ('grade_e4', 'E4'),
                                 ('grade-e5', 'E5'), ('grade_ex1', 'EX-1'), ('grade_a1', 'A1'), ('grade_a2', 'A2'),
                                 ('grade_a3', 'A3')], 'Grade')
    ns_currency_id = fields.Many2one('res.currency', string='Currency')
    ns_commuting_cost = fields.Float(string="Commuting Cost")
    ns_annual_base_salary = fields.Monetary(string="Annual Base Salary", currency_field="ns_currency_id")
    ns_incentive_plan = fields.Selection([('bonus', 'Annual Bonus Plan'), ('sales', 'Sales Incentive Plan')], 'Incentive Plan')
    ns_annual_bonus_plan = fields.Float(string="Annual Bonus Plan (% of base salary)")
    ns_sales_incentive_plan = fields.Float(string="Sales Incentive Plan (% of base salary)")
    ns_annual_total_target_compensation = fields.Monetary(string='Annual Total Target Compensation', currency_field="ns_currency_id", readonly=True)
    ns_carry_points = fields.Integer(string="Carry Points")
    ns_payroll_number = fields.Char(string="Payroll Number")
    ns_bank_name = fields.Char(string="Name of Bank")
    ns_account_holder = fields.Char(string="Name of Account Holder")
    ns_account_number = fields.Char(string="Account No")
    ns_swift_code = fields.Char(string="SWIFT Code")
