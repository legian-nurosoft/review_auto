# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import re, json
import logging
_logger = logging.getLogger(__name__)

TICKET_PRIORITY = [
    ('0', 'S-4'),
    ('1', 'S-3'),
    ('2', 'S-2'),
    ('3', 'S-1'),
]

class HelpdeskTicketInherit(models.Model):
    _inherit = 'helpdesk.ticket'

    ns_requested_service_date = fields.Datetime(string='Requested Service Date', tracking=100)
    ns_ticket_subject = fields.Char(string='Ticket Subject')
    ns_team_id_name = fields.Char(string='Team Name', related='team_id.name')

    nrs_ref_task_id = fields.Many2one('project.task', 'Task ID')
    nrs_total_time_spent = fields.Float('Hours Spent')
    # nrs_timesheet = fields.One2many('account.analytic.line', 'ns_project_id', string='Timesheet',
    #                                compute='_get_helpdesk_timesheet')
    
    team_id = fields.Many2one(tracking=100)
    partner_id = fields.Many2one(tracking=100)
    ticket_type_id = fields.Many2one(tracking=100)

    priority = fields.Selection(TICKET_PRIORITY, string='Severity', default='0', tracking=100)

    # site access
    ns_site_visit_date_end = fields.Datetime(tracking=100, string="Site Visit Date End")
    ns_site_visit_date_start = fields.Datetime(tracking=100, string="Site Visit Date Start")
    ns_special_visit_area = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Special Visit Area')
    ns_special_visit_area_name = fields.Char(string='Visit Area', tracking=100)

    # shipment
    ns_shipment_date_end = fields.Datetime(tracking=100, string="Shipment Date End")
    ns_shipment_date_start = fields.Datetime(tracking=100, string="Shipment Date Start")
    ns_courier_company = fields.Char(string='Courier Company')
    ns_handling_instruction = fields.Selection([
            ('service_area', 'Leave items in my service area'),
            ('temporary_storage', 'Leave items in temporary storage')
        ], string='Handling Instructions', tracking=100)
    ns_shipment_detail_ids = fields.Many2many('ns.helpdesk.ticket.shipment.detail',string='Shipment Detail')
    ns_site_access_detail_ids = fields.Many2many('ns.helpdesk.ticket.site.access.detail')
    ns_site_access_approve_button_visibility =  fields.Boolean('Display Site Access Approve Button', compute='_compute_site_access_approve_button_visibility')
    ns_site_access_submit_button_visibility =  fields.Boolean('Display Site Access Submit Button', compute='_compute_site_access_submit_button_visibility')
    ns_shipment_approve_button_visibility =  fields.Boolean('Display Shipment Approve Button', compute='_compute_shipment_submit_button_visibility')
    ns_service_id = fields.Many2one('project.task',string='Service ID')

    def site_access_approve(self):
        stage_name = self.stage_id.name
        stage = self.env['helpdesk.stage'].search([('team_ids.id',"=",self.team_id.id)])
        user_check = False
        stage_inprogress = 0
        for res in stage:
            if res.name == stage_name:
                for res2 in res.ns_approver_ids:
                    if self.env.user.name == res2.name:
                        user_check = True
            if res.name =="Approved":
                stage_inprogress = res.id
        if not user_check:
            raise Warning(_('You have no access to approve this ticket'))
        self.stage_id = stage_inprogress

    def site_access_submit(self):
        stage = self.env['helpdesk.stage'].search([('team_ids.id',"=",self.team_id.id)])
        special_visitor = self.ns_special_visit_area
        # raise Warning(_(special_visitor))
        for res in stage:
            if special_visitor == "no":
                if res.name == "Approved":
                    self.stage_id = res.id
            if special_visitor == "yes":
                if res.name == "Pending Approval":
                    self.stage_id = res.id

    # def _get_helpdesk_timesheet(self):
    #     for project in self:
    #         remote_hand = self.env['helpdesk.ticket'].search([('nrs_ref_task_id', '=', project.id)])
    #         timesheet_line = self.env['account.analytic.line'].search([('nrs_ref_task_id', '=', project.id)])
    #
    #     total_time = 0
    #     time_left = 0
    #
    #     for line in remote_hand.timesheet_ids:
    #         total_time += line.unit_amount
    #         timesheet_line += line
    #
    #     project.nrs_timesheet = timesheet_line
    #     project.nrs_total_time_spent = total_time

    def _compute_site_access_approve_button_visibility(self):
        is_site_access = False
        for res in self.team_id:
            if 'Site Access' in res.name:
                is_site_access = True
        for record in self:
            if record.stage_id.name in ['Pending Approval'] and is_site_access == True:
                record.ns_site_access_approve_button_visibility = True
            else:
                record.ns_site_access_approve_button_visibility = False
    def _compute_site_access_submit_button_visibility(self):
        is_site_access = False
        for res in self.team_id:
            if 'Site Access' in res.name:
                is_site_access = True
        for record in self:
            if record.stage_id.name in ['New'] and is_site_access == True:
                record.ns_site_access_submit_button_visibility = True
            else:
                record.ns_site_access_submit_button_visibility = False

    def write(self, vals):
        if 'Shipment' in self.team_id.name:
            stage_id=vals.get('stage_id',False)
            stage_name = self.env['helpdesk.stage'].search([('id',"=",stage_id)])
            stage_action = False
            for stage in stage_name:
                if stage.name == "Approved (Inbound)" or stage.name == "Approved (Outbound)":
                    stage_action = True
            logger = logging.info(stage_name)
            if self.stage_id.name == "New"  and stage_action:
                if self.x_studio_loading_dock_required:
                    pending_stage = self.env['helpdesk.stage'].search([('team_ids.id',"=",self.team_id.id)])
                    for res in pending_stage:
                        if res.name == "Pending Approval":
                            vals['stage_id'] = res.id
                else:
                    vals['stage_id'] = stage_id
        res = super(HelpdeskTicketInherit, self).write(vals)
        return res

    def _compute_shipment_submit_button_visibility(self):
        is_shipment = False
        for res in self.team_id:
            if 'Shipment' in res.name:
                is_shipment = True
        for record in self:
            if record.stage_id.name in ['Pending Approval'] and is_shipment == True:
                record.ns_shipment_approve_button_visibility = True
            else:
                record.ns_shipment_approve_button_visibility = False
    
    def shipment_approve(self):
        stage_name = self.stage_id.name
        stage = self.env['helpdesk.stage'].search([('team_ids.id',"=",self.team_id.id)])
        user_check = False
        stage_inprogress = 0
        ticket_type = 'Approved (Inbound)' if self.ticket_type_id.name == 'Inbound' else 'Approved (Outbound)'
        
        for res in stage:
            if res.name == stage_name:
                for res2 in res.ns_approver_ids:
                    if self.env.user.name == res2.name:
                        user_check = True
            if res.name == ticket_type:
                stage_inprogress = res.id
        logger = logging.info(stage_inprogress)
        if not user_check:
            raise Warning(_('You have no access to approve this ticket'))
        self.stage_id = stage_inprogress
    
    ns_partner_domain = fields.Many2many('res.partner', compute='compute_partner_domain', store=False)
    # ns_studio_operation_site = fields.Many2one('operating.sites', string="Operation Site")
    # ns_studio_visit_date = fields. string="Visit Date"
    # ns_studio_special_visit_area = fields string="Special Visit Area"
    # ns_studio_requested_visitor = fields string="Requested Visitor's Name"
    # ns_studio_requested_visitor_identification_number = fields string="Requested Visitor Identification Number"
    # ns_studio_loading_dock_required = fields string="Loading Dock Required"
    # ns_studio_free_due_date = fields string="Free Due Date"
    # ns_studio_charge_due_date = fields string="Charge Due Date"
    # ns_studio_shipment_date = fields  string="Expected Delivery Date"
    # ns_studio_number_of_shipment = fields string="Number of Shipment"
    # ns_studio_shipment_tracking_number = fields string="Shipment Tracking Number"
    # ns_studio_free_charge = fields string="Free Charge"
    # ns_studio_rejected_reason = fields string="Rejected Reason"
    # ns_studio_timesheet_product = fields 
    service_ids = fields.Many2many('project.task', compute="compute_service_ids", store=False)
    ns_designated_company = fields.Many2one('res.partner', string="Designated Company", domain="[('nrs_company_type', '!=', 'person')]")
    

    @api.depends('team_id')
    def compute_partner_domain(self):
        if re.search("^(remote)|(site)|(shipment)|(fault).+", self.team_id.name.lower()):
            partner = self.env['res.partner'].search(['&', '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id), ('nrs_company_type', '=', 'person')])
        else:
            partner = self.env['res.partner'].search(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])
        self.ns_partner_domain = partner.ids
    
    @api.onchange('team_id', 'x_studio_operation_site', 'ns_designated_company')
    def compute_service_ids(self):
        if re.search("^(remote)|(site)|(shipment).+", self.team_id.name.lower()):
            return {'domain': {'ns_service_id': [('x_studio_operation_site','=',self.x_studio_operation_site.id),('partner_id','=',self.ns_designated_company.id),('project_id.name','in',['Installed Base ID', 'Installed Base JP', 'Installed Base CN', 'Installed Base KR']),('x_studio_product.categ_id.name','in',['Space'])]}}
        else:
            return {'domain': {'ns_service_id': [('x_studio_operation_site','=',self.x_studio_operation_site.id),('partner_id','=',self.ns_designated_company.id),('project_id.name','in',['Installed Base ID', 'Installed Base JP', 'Installed Base CN', 'Installed Base KR'])]}}

class AllowedTicket(models.Model):
    _name = 'nrs.allowed.ticket.type'

    name = fields.Char(string='Ticket Name')
    nrs_type = fields.Selection([
            ('remote_hands', 'Remote Hands'),
            ('fault_report', 'Fault Report'),
            ('Site Access', 'Site Access'),
            ('Shipment', 'Shipment')
        ], string='Type')
    nrs_ticket_type_ids = fields.Many2many('helpdesk.ticket.type',string='Allowed Ticket Type')


class ServiceSelection(models.Model):
    _name = 'nrs.req.service.selection'

    name = fields.Char()
    nrs_selection_value = fields.Char(string='Value')
    nrs_selection_type = fields.Selection([
            ('choose_service', 'Choose Service'),
            ('intra_customer', 'Intra Customer'),
            ('media_type', 'Media Type'),
            ('nrc_postfix', 'NRC Postfix')
        ], string='Type')

class NRSNotification(models.Model):
    _name = 'nrs.notification'
    _rec_name = 'nrs_subject'

    nrs_subject = fields.Char('Subject')
    nrs_body = fields.Text('Body')
    nrs_start_date = fields.Date('Start Date')
    nrs_end_date = fields.Date('End Date')
    nrs_domain = fields.Char('Domain')
    nrs_ignore_partner_id = fields.Char(copy=False)

class MailMessage(models.Model):
    _inherit = 'mail.message'

    nrs_ignore_partner_id = fields.Char(copy=False)

class HelpdeskTicketShipmentDetail(models.Model):
    _name = 'ns.helpdesk.ticket.shipment.detail'

    ns_shipment_detail_item_number = fields.Integer(string='Item Number')
    ns_shipment_detail_dimension = fields.Char(string='Shipment Dimension')
    ns_shipment_detail_weight = fields.Integer(string='Shipment Weight')
    ns_shipment_detail_tracking_number = fields.Char(string='Shipment Tracking Number')
    ns_shipment_detail_dispatched = fields.Boolean(string='Dispatched')
    ns_shipment_detail_storage_location = fields.Char(string='Storage Location')
    ns_uom = fields.Many2one('uom.uom', 'Shipment Weight UOM', domain="[('category_id.id', '=', 2)]")

class HelpdeskTicketSiteAccessDetail(models.Model):
    _name = 'ns.helpdesk.ticket.site.access.detail'

    ns_site_access_detail_visitor_name = fields.Char(string='Visistor Name')
    ns_site_access_detail_visitor_id_number = fields.Char(string='Visitor Id Number')

class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    ns_approver_ids = fields.Many2many('res.users')
    ns_is_approvers_on =fields.Boolean(string='Is Aprrover On', default=False)

    @api.onchange('team_ids')
    def _onchange_team_id(self):
        self.ns_is_approvers_on = False
        for res in self.team_ids:
            if 'Site Access' in res.name:
                self.ns_is_approvers_on = True
            if 'Shipment' in res.name:
                self.ns_is_approvers_on = True

    

