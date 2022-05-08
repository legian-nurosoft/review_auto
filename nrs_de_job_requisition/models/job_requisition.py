# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _


class JobRequisition(models.Model):
    _name = "ns.job.requisition"
    _description = "Job Requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ns_number'
    _order = 'ns_sequence asc, ns_name asc, id desc'

    def _default_ns_user_id(self):
        return self.env.user.id

    ns_number = fields.Char('Number', copy=False)
    ns_name = fields.Char('Requisition')
    ns_active = fields.Boolean('Active')
    ns_priority = fields.Boolean('High Priority')
    ns_role_job_title = fields.Char('Role Job Title')
    ns_date_of_request = fields.Date('Date of Request')
    ns_available_positions = fields.Integer('Available positions')
    ns_sequence = fields.Integer('Sequence')
    ns_expected_work_hours = fields.Selection([
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time')
        ], string='Weekly Working Hours')
    ns_job_requisition_id_hr_job_count = fields.Integer('Job Requisition count', compute='_compute_ns_job_requisition_id_hr_job_count')
    ns_department_id = fields.Many2one('hr.department', 'Business Unit / Department')
    ns_stage_id = fields.Many2one('ns.job.requisition.stage', group_expand='_read_group_stage_ids')
    ns_user_id = fields.Many2one('res.users', string='Hiring Manager', domain="[('share', '=', False)]", default=_default_ns_user_id)
    ns_hiring_managers_manager = fields.Many2one('hr.employee', string='Hiring Manager’s Manager')
    ns_currency_id = fields.Many2one('res.currency', string='Currency')
    ns_usd_currency_id = fields.Many2one('res.currency', string='Currency',
                                         default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    ns_type_of_position = fields.Selection([
            ('employee', 'Employee'),
            ('fixed_term_contract_employee', 'Fixed Term Contract Employee'),
            ('independent_consultant', 'Independent Consultant')
        ], string='Type of Position')
    ns_kanban_state = fields.Selection([
            ('normal', 'In Progress'),
            ('done', 'Ready'),
            ('blocked', 'Blocked')
        ], string='Status')
    ns_notes = fields.Text(string='Notes')
    ns_reason_for_hire = fields.Selection([
            ('budgeted', 'New (Budgeted)'),
            ('non_budgeted', 'New (Non Budgeted)'),
            ('replacement', 'Replacement')
        ], string='Reason for hire')
    ns_hr_job_count = fields.Integer(string='Job Count', compute='_compute_ns_hr_job_count')
    ns_maximum_no_hours = fields.Float(string='Maximum no. Hours')
    ns_work_location = fields.Selection([
            ('osaka', 'Osaka'),
            ('hong_kong', 'Hong Kong'),
            ('singapore', 'Singapore'),
            ('korea', 'Korea'),
            ('shanghai', 'Shanghai'),
            ('beijing', 'Beijing'),
            ('philippines', 'Philippines'),
            ('usa', 'USA'),
            ('indonesia', 'Indonesia'),
            ('tokyo', 'Tokyo')
        ], string='Work Location')
    ns_hire_group = fields.Selection([
            ('corporate', 'Corporate Head Office'),
            ('project', 'Country/Project')
        ], string='Hire Group')
    ns_project_name = fields.Char(string='Project Name')
    ns_digital_edge_legal_entity = fields.Many2one('res.company', string='Digital Edge Legal Entity')
    ns_role_purpose_and_key_kpis = fields.Text(string='Role Purpose and Key KPIs')
    ns_key_responsibilities = fields.Text(string='Key Responsibilities')
    ns_successful_candidate_criteria = fields.Text(string='Successful Candidate Criteria')
    ns_business_justification_for_hire = fields.Text(string='Business Justification for Hire')
    ns_primary_job_posting_location = fields.Selection([
        ('osaka', 'Osaka'),
        ('hong_kong', 'Hong Kong'),
        ('singapore', 'Singapore'),
        ('korea', 'Korea'),
        ('shanghai', 'Shanghai'),
        ('beijing', 'Beijing'),
        ('philippines', 'Philippines'),
        ('usa', 'USA'),
        ('indonesia', 'Indonesia'),
        ('tokyo', 'Tokyo')
    ], string='Primary Job Posting Location')
    ns_other_job_posting_location = fields.Selection([
        ('osaka', 'Osaka'),
        ('hong_kong', 'Hong Kong'),
        ('singapore', 'Singapore'),
        ('korea', 'Korea'),
        ('shanghai', 'Shanghai'),
        ('beijing', 'Beijing'),
        ('philippines', 'Philippines'),
        ('usa', 'USA'),
        ('indonesia', 'Indonesia'),
        ('tokyo', 'Tokyo')
    ], string='Other Job Posting Location')
    ns_email_recipient = fields.Char(string='Email Recipient', compute='_compute_ns_email_recipient')
    ns_erp_access_url = fields.Char(string='View Url',compute='_compute_ns_erp_access_url')
    ns_annual_base_salary = fields.Monetary(string='Annual Base Salary', currency_field="ns_currency_id")
    ns_annual_base_salary_commision = fields.Monetary(string='Annual Base Salary', currency_field="ns_currency_id")
    ns_annual_bonus_amount = fields.Monetary(string='Annual Bonus Amount', currency_field="ns_currency_id")
    ns_annual_bonus_plan = fields.Float(string='Annual Bonus Plan (% of base salary)')
    ns_total_target_compensation_ttc = fields.Monetary(string='Total Target Compensation (TTC)', currency_field="ns_currency_id")
    ns_total_target_compensation_ttc_commision = fields.Monetary(string='Total Target Compensation (TTC)', currency_field="ns_currency_id")
    ns_annual_base_salary_usd = fields.Monetary(string='Annual Base Salary (USD)', currency_field="ns_usd_currency_id")
    ns_annual_base_salary_usd_commision = fields.Monetary(string='Annual Base Salary (USD)', currency_field="ns_usd_currency_id")
    ns_annual_bonus_amount_usd = fields.Monetary(string='Annual Bonus Amount (USD)', currency_field="ns_usd_currency_id")
    ns_total_target_compensation_ttc_usd = fields.Monetary(string='Total Target Compensation (TTC) (USD)', currency_field="ns_usd_currency_id")
    ns_total_target_compensation_ttc_usd_commision = fields.Monetary(string='Total Target Compensation (TTC) (USD)', currency_field="ns_usd_currency_id")
    ns_sales_commission_amount = fields.Monetary(string='Sales Commission Amount', currency_field="ns_currency_id")
    ns_sales_commission_plan = fields.Float(string='Sales Commission Plan (% of base and pay mix)')
    ns_sales_commission_amount_usd = fields.Monetary(string='Sales Commission Amount (USD)', currency_field="ns_usd_currency_id")
    ns_total_target_compensation_ttc_usd_sales = fields.Monetary(string='Total Target Compensation (TTC) (USD)', currency_field="ns_usd_currency_id")
    ns_is_approval_stage = fields.Boolean(string='Is Approval Stage', related='ns_stage_id.ns_is_approval_stage')
    ns_show_submit_button = fields.Boolean(string='Show Submit Button', related='ns_stage_id.ns_show_submit_button')
    ns_show_approve_button = fields.Boolean(string='Show Approve Button', related='ns_stage_id.ns_show_approve_button')
    ns_show_reject_button = fields.Boolean(string='Show Reject Button', related='ns_stage_id.ns_show_reject_button')

    @api.onchange('ns_user_id')
    def ns_user_id_onchange(self):
        if self.ns_user_id:
            self.ns_hiring_managers_manager = self.ns_user_id.employee_parent_id.id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['ns.job.requisition.stage'].search([])
        return stage_ids

    def _compute_ns_hr_job_count(self):
        results = self.env['hr.job'].read_group([('ns_job_requisition_id', 'in', self.ids)], ['ns_job_requisition_id'], ['ns_job_requisition_id'])
        dic = {}
        for x in results:
            dic[x['ns_job_requisition_id'][0]] = x['ns_job_requisition_id_count']
        for record in self:
            record['ns_hr_job_count'] = dic.get(record.id, 0)

    def _compute_ns_job_requisition_id_hr_job_count(self):
        results = self.env['hr.job'].read_group([('ns_job_requisition_id', 'in', self.ids)], ['ns_job_requisition_id'], ['ns_job_requisition_id'])
        dic = {}
        for x in results:
            dic[x['ns_job_requisition_id'][0]] = x['ns_job_requisition_id_count']
        for record in self:
            record['ns_job_requisition_id_hr_job_count'] = dic.get(record.id, 0)

    def job_requisition_action_submit(self):
        for rec in self:
            next_stage = self.env['ns.job.requisition.stage'].search([('ns_sequence','>',rec.ns_stage_id.ns_sequence)], order='ns_sequence asc', limit=1)
            if next_stage:
                rec.ns_stage_id = next_stage.id

    def job_requisition_action_approve(self):
        for rec in self:
            if self.env.user.id not in rec.ns_stage_id.ns_approver_ids.ids:
                raise exceptions.UserError(_("You don't have permission to perform this action."))

            next_stage = self.env['ns.job.requisition.stage'].search([('ns_sequence','>',rec.ns_stage_id.ns_sequence)], order='ns_sequence asc', limit=1)
            if next_stage:
                rec.ns_stage_id = next_stage.id
                if next_stage.ns_is_approval_stage:
                    self.env['hr.job'].create({
                        'name': '[%s] %s' % (rec.ns_number, rec.ns_name),
                        'ns_job_requisition_id': rec.id,
                        'department_id': rec.ns_department_id.id,
                        'ns_hiring_manager_id': rec.ns_user_id.id,
                        'ns_hiring_managers_manager': rec.ns_hiring_managers_manager.id,
                        'no_of_recruitment': rec.ns_available_positions,
                        'ns_date_of_request': rec.ns_date_of_request,
                        'ns_type_of_position': rec.ns_type_of_position,
                        'ns_work_location': rec.ns_work_location
                    })

    def job_requisition_action_reject(self):
        for rec in self:
            next_stage = self.env['ns.job.requisition.stage'].search([('ns_is_rejected_stage','=',True)], limit=1)
            if next_stage:
                rec.ns_stage_id = next_stage.id

    @api.model
    def create(self, vals):
        seq_date = fields.Datetime.now()
        if vals.get('ns_date_of_request'):
            seq_date = fields.Date.to_date(vals['ns_date_of_request'])
        vals['ns_number'] = self.env['ir.sequence'].with_context({'ir_sequence_date': seq_date, 'month_date_range': 1}).next_by_code('ns.job.requisition') or _('New')

        return super(JobRequisition, self).create(vals)

    def name_get(self):
        self.browse(self.ids).read(['ns_number', 'ns_name'])
        return [(jreq.id, '%s%s' % (jreq.ns_number and '[%s] ' % jreq.ns_number or '', jreq.ns_name)) for jreq in self]

    def write(self, vals):
        res = super(JobRequisition, self).write(vals)

        if vals.get('ns_stage_id', False):
            for rec in self:
                if rec.ns_stage_id.ns_template_id:
                    rec.with_context(force_send=True).message_post_with_template(rec.ns_stage_id.ns_template_id.id, composition_mode='comment', email_layout_xmlid="nrs_de_job_requisition.mail_notification_blank")

        return res

    def _compute_ns_email_recipient(self):
        for rec in self:
            email_recipient = []
            if rec.ns_stage_id.ns_send_email_to_hiring_manager and rec.ns_user_id:
                email_recipient.append(str(rec.ns_user_id.partner_id.id))
            
            if rec.ns_stage_id.ns_send_email_to_approver:
                for approver in rec.ns_stage_id.ns_approver_ids:
                    email_recipient.append(str(approver.partner_id.id))
            
            rec.ns_email_recipient = ','.join(x for x in email_recipient)

    def _compute_ns_erp_access_url(self):
        erp_domain = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url')
        menu = self.env.ref('nrs_de_job_requisition.menu_ns_job_requisition')
        for rec in self:
            rec.ns_erp_access_url = 'http://%s/web#menu_id=%s&id=%s&model=ns.job.requisition&view_type=form' % (erp_domain, str(menu.id), str(rec.id))
            

    def get_currency_conversion(self, amount, from_currency, to_currency):
        current_date = str(fields.Date.context_today(self))
        fx_rate = self.env['crm.fx.rate']
        from_rate = fx_rate.search([('date_start', '<=', current_date), ('currency_id', '=', from_currency.id), ('date_end', '>=', current_date)], order='date_start desc', limit=1)
        to_rate = fx_rate.search([('date_start', '<=', current_date), ('currency_id', '=', to_currency.id), ('date_end', '>=', current_date)], order='date_start desc', limit=1)
        if from_rate and to_rate:
            return to_currency.round(amount * (to_rate.rate / from_rate.rate))
        else:
            return 0
    
    # local
    @api.onchange('ns_currency_id','ns_annual_base_salary')
    def ns_annual_base_salary_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_base_salary':
            self.ns_annual_base_salary_usd = self.get_currency_conversion(self.ns_annual_base_salary, self.ns_currency_id, self.ns_usd_currency_id)

    @api.onchange('ns_currency_id','ns_annual_base_salary_commision')
    def ns_annual_base_salary_commision_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_base_salary_commision':
            self.ns_annual_base_salary_usd_commision = self.get_currency_conversion(self.ns_annual_base_salary_commision, self.ns_currency_id, self.ns_usd_currency_id)

    @api.onchange('ns_currency_id','ns_annual_bonus_amount')
    def ns_annual_bonus_amount_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_bonus_amount':
            self.ns_annual_bonus_amount_usd = self.get_currency_conversion(self.ns_annual_bonus_amount, self.ns_currency_id, self.ns_usd_currency_id)
            
    @api.onchange('ns_currency_id','ns_total_target_compensation_ttc')
    def ns_total_target_compensation_ttc_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_total_target_compensation_ttc':
            self.ns_total_target_compensation_ttc_usd = self.get_currency_conversion(self.ns_total_target_compensation_ttc, self.ns_currency_id, self.ns_usd_currency_id)

    @api.onchange('ns_currency_id','ns_total_target_compensation_ttc_commision')
    def ns_total_target_compensation_ttc_commision_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_total_target_compensation_ttc_commision':
            self.ns_total_target_compensation_ttc_usd_commision = self.get_currency_conversion(self.ns_total_target_compensation_ttc_commision, self.ns_currency_id, self.ns_usd_currency_id)

    @api.onchange('ns_currency_id','ns_sales_commission_amount')
    def ns_sales_commission_amount_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_sales_commission_amount':
            self.ns_sales_commission_amount_usd = self.get_currency_conversion(self.ns_sales_commission_amount, self.ns_currency_id, self.ns_usd_currency_id)
    
    
    # USD
    @api.onchange('ns_currency_id','ns_annual_base_salary_usd')
    def ns_annual_base_salary_usd_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_base_salary_usd':
            self.ns_annual_base_salary = self.get_currency_conversion(self.ns_annual_base_salary_usd, self.ns_usd_currency_id, self.ns_currency_id)

    @api.onchange('ns_currency_id','ns_annual_base_salary_usd_commision')
    def ns_annual_base_salary_usd_commision_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_base_salary_usd_commision':
            self.ns_annual_base_salary_commision = self.get_currency_conversion(self.ns_annual_base_salary_usd_commision, self.ns_usd_currency_id, self.ns_currency_id)

    @api.onchange('ns_currency_id','ns_annual_bonus_amount_usd')
    def ns_annual_bonus_amount_usd_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_annual_bonus_amount_usd':
            self.ns_annual_bonus_amount = self.get_currency_conversion(self.ns_annual_bonus_amount_usd, self.ns_usd_currency_id, self.ns_currency_id)

    @api.onchange('ns_currency_id','ns_total_target_compensation_ttc_usd')
    def ns_total_target_compensation_ttc_usd_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_total_target_compensation_ttc_usd':
            self.ns_total_target_compensation_ttc = self.get_currency_conversion(self.ns_total_target_compensation_ttc_usd, self.ns_usd_currency_id, self.ns_currency_id)

    @api.onchange('ns_currency_id','ns_total_target_compensation_ttc_usd_commision')
    def ns_total_target_compensation_ttc_usd_commision_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_total_target_compensation_ttc_usd_commision':
            self.ns_total_target_compensation_ttc_commision = self.get_currency_conversion(self.ns_total_target_compensation_ttc_usd_commision, self.ns_usd_currency_id, self.ns_currency_id)

    @api.onchange('ns_currency_id','ns_sales_commission_amount_usd')
    def ns_sales_commission_amount_usd_onchange(self):
        if self.ns_currency_id and self.ns_usd_currency_id and self._context.get('field_changed','') == 'ns_sales_commission_amount_usd':
            self.ns_sales_commission_amount = self.get_currency_conversion(self.ns_sales_commission_amount_usd, self.ns_usd_currency_id, self.ns_currency_id)
