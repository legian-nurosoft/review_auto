from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.osv import expression


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    ns_order_line_readonly = fields.Boolean(compute="get_readonly_orderline")
    subscription_count = fields.Integer(compute='_compute_subscription_count_inherit')
    ns_can_edit_so = fields.Boolean('Can Edit SO', compute='_compute_ns_can_edit_so', default=True)

    def _compute_ns_can_edit_so(self):
        for rec in self:
            if self.env.user.has_group('base.group_system'):
                rec.ns_can_edit_so = True
            else:
                if rec.approval_state in ['sale','done','cancel']:
                    rec.ns_can_edit_so = False
                else:
                    rec.ns_can_edit_so = True

    def _compute_subscription_count_inherit(self):
        """Compute the number of distinct subscriptions linked to the order."""
        for order in self:
            sub_count = len(self.env['sale.order.line'].with_context({'ignore_access_right': 1}).read_group([('order_id', '=', order.id), ('subscription_id', '!=', False)],
                                                    ['subscription_id'], ['subscription_id']))
            order.subscription_count = sub_count

    def get_readonly_orderline(self):
        acc = self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_ops')
        for rec in self: 
            rec.ns_order_line_readonly = acc 

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_domain = []
        
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])
        
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])
            
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|', ('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])
               
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])
        
        domain += new_domain

        return super(SalesOrder, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        new_domain = []
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])
        
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|',('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])
        
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])
        
        domain += new_domain
        print(domain,'domainnn')
        return super(SalesOrder, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def search_count(self, args):
        new_domain = []
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])
        
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|',('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('opportunity_id.x_studio_a_end_sales', '=', self.env.user.id), ('opportunity_id.x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])
        
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])
        args += new_domain


        return super(SalesOrder, self).search_count(args)


    def write(self, vals):
        if 'ns_from_ui' in self._context and self.approval_state in ['preapproved','approved']:
            vals['approval_state'] = 'draft'
            vals['state'] = 'draft'

        return super(SalesOrder, self).write(vals)



class SalesOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        
        if 'ignore_access_right' not in self._context:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
                members = []
                for team in sale_team:
                    members += team.member_ids.ids
                # domain += ['|', ('salesman_id', '=', self.env.user.id), ('salesman_id', 'in', members)]
            elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
                sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
                members = []
                for team in sale_team:
                    members += team.member_ids.ids + team.user_id.ids
                domain += ['|', ('salesman_id', '=', self.env.user.id), ('salesman_id', 'in', members)]
        return super(SalesOrderLine, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            domain += ['|', ('salesman_id', '=', self.env.user.id), ('salesman_id', 'in', members)]
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            domain += ['|', ('salesman_id', '=', self.env.user.id), ('salesman_id', 'in', members)]
        return super(SalesOrderLine, self).search_read(domain, fields, offset, limit, order)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_domain = []
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])

        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids

            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support') :
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])
        
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])

        domain += new_domain

        return super(CrmLead, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        new_domain = []
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])

        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])


        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])
        
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support') :
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])

        domain += new_domain
        return super(CrmLead, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def search_count(self, args):
        new_domain = []
        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
            sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids
            if len(members) > 0:
                manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, manager_domain])

        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            members = []
            for team in sale_team:
                members += team.member_ids.ids + team.user_id.ids
            if len(members) > 0:
                country_manager_domain = ['|', ('user_id', '=', self.env.user.id), ('user_id', 'in', members)]
                new_domain = expression.OR([new_domain, country_manager_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep') and self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            representative_domain = ['&', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
            new_domain = expression.OR([new_domain, representative_domain])
        elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_rep'):
            representative_domain = ['&', '|', '|', '|', ('x_studio_a_end_sales', '=', self.env.user.id), ('x_studio_b_end_sales', '=', self.env.user.id), ('user_id', '=', self.env.user.id), ('user_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)]
            new_domain = expression.OR([new_domain, representative_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_cont_manager'):
            
            sale_team = self.env['crm.team'].search([('ns_leader_country', '=', self.env.user.id)])
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_manager'):
                    sale_team = self.env['crm.team'].search([('user_id', '=', self.env.user.id)])
            o_countries = []
            if sale_team:
                for team in sale_team:
                    if team.x_studio_operation_country:
                        o_countries.append(team.x_studio_operation_country.id)
            if o_countries:
                country_domain = [('x_studio_operation_country','in',o_countries)]
                new_domain = expression.OR([new_domain, country_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_deal_desk') or self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_reg_manager'):
            user = self.env.user
            regional_domain = [('company_id', 'in', user.company_ids.ids)]
            new_domain = expression.OR([new_domain, regional_domain])

        if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
            user = self.env.user
            regional_domain = [('company_id', '=', user.company_id.id)]
            new_domain = expression.OR([new_domain, regional_domain])

        args += new_domain

        return super(CrmLead, self).search_count(args)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        self.env['ir.model.access'].call_cache_clearing_methods()
        return res


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    ns_leader_country = fields.Many2one('res.users', "Leader Country")

