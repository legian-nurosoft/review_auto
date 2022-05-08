# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, MissingError, AccessError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #name = fields.Char(string='Order Reference', required=False, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))

    ns_special_billing_instruction = fields.Boolean(string="Special Billing Instructions", default=False, track_visibility='onchange', tracking=True)
    ns_special_billing_user_restriction = fields.Boolean(string="User Restriction", compute='_check_user_group')

    ns_special_billing_instruction_ids = fields.One2many('ns.special.billing.instruction', 'ns_order_id', string='Special Billing Instruction Lines', track_visibility='onchange', tracking=True)

    ns_temp_sbi = fields.Boolean(compute='_sbi_current_set')
    ns_sbi_changed = fields.Boolean(compute='_sbi_current_set')

    # 0 = not confirmed, 1 = confirmed by nrs_group_sale_support, 2 = confirmed by group_account_manager, 3 = confirmed by both
    ns_confirmed = fields.Integer(default=0)

    # To check later whether or not ns_special_billing_instruction has been changed
    def _sbi_current_set(self):
        self.ns_temp_sbi = self.ns_special_billing_instruction
        self.ns_sbi_changed = False

    @api.onchange('ns_special_billing_instruction')
    def _update_sbi_changed(self):
        if self.ns_special_billing_instruction != self.ns_temp_sbi:
            self.ns_sbi_changed = True
        else:
            self.ns_sbi_changed = False

    @api.onchange('ns_special_billing_instruction')
    def field_visibility(self):
        for record in self:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                record.ns_special_billing_user_restriction = True

    def _check_user_group(self):
        # Check the user have Sale Support privileges
        for record in self:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                record.ns_special_billing_user_restriction = True
            else:
                record.ns_special_billing_user_restriction = False

    def write(self, vals):
        # One2many "ns_special_billing_instruction_ids" validation
        if self.ns_special_billing_instruction or \
        ('ns_special_billing_instruction' in vals and vals['ns_special_billing_instruction']):
            if not ('ns_special_billing_instruction' in vals and not vals['ns_special_billing_instruction']):
                if not ('ns_special_billing_instruction_ids' in vals or self.ns_special_billing_instruction_ids):
                    raise ValidationError('Please add at least one Special Billing Instruction')
                elif 'ns_special_billing_instruction_ids' in vals:
                    links = 0 # Number of rec that will be added from One2many
                    unlinks = 0 # Number of rec that will be deleted from One2many

                    for inst in vals['ns_special_billing_instruction_ids']:
                        flag = inst[0]
                        if flag == 0:
                            links += 1
                        elif flag == 1:
                            True
                        elif flag == 2:
                            unlinks += 1
                        elif flag == 3:
                            unlinks += 1
                        elif flag == 4:
                            unlinks += 1
                        elif flag == 5:
                            if links == 0:
                                raise ValidationError('Please add at least one Special Billing Instruction')
                    
                    # Check if there will be no record in the One2many
                    if len(self.ns_special_billing_instruction_ids) + links - unlinks < 1:
                        raise ValidationError('Please add at least one Special Billing Instruction')


        # Update Special Billing Instruction field in Sales Subscription
        if 'ns_special_billing_instruction' in vals:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                if vals['ns_special_billing_instruction'] == True:
                    email_addresses = []
                    advisor_group = self.env.ref('account.group_account_manager')
                    if advisor_group == None or advisor_group == False:
                        raise MissingError('The group account.group_account_manager does not exist!')
                    else:
                        if len(advisor_group.users) == 0:
                            raise MissingError(f'The group "{advisor_group.full_name}" does not have any users!')
                        else:
                            for user in advisor_group.users:
                                if user.email:
                                    email_addresses.append(user.email)
                        if len(email_addresses) == 0:
                            raise MissingError(f'None of the users in the group "{advisor_group.full_name}" has an email to send to!')

                    sale_order_id = self.id
                    subscription = self.env['sale.subscription'].search([('x_studio_original_sales_order', '=',
                                                                          sale_order_id)])
                    if subscription:
                        subscription.write({'ns_special_billing_instruction': True})

                    template_id = self.env.ref('nrs_de_special_billing_instructions.special_billing_instructions_approval').id
                    
                    emails = ','.join(email_addresses)
                    self.env['mail.template'].browse(template_id).with_context(emails=emails).send_mail(self.id, force_send=True)

                if vals['ns_special_billing_instruction'] == False:
                    sale_order_id = self.id
                    subscription = self.env['sale.subscription'].search([('x_studio_original_sales_order', '=',
                                                                          sale_order_id)])
                    if subscription:
                        subscription.write({'ns_special_billing_instruction': False})

                    to_unlink = []
                    for line in self.ns_special_billing_instruction_ids:
                        to_unlink.append(line.id)
                    vals['ns_special_billing_instruction_ids'] = False
                    self.env['ns.special.billing.instruction'].browse(to_unlink).unlink()
                    
            else:
                raise UserError("You don't have permission to update Special Billing Instructions !!!! ")
        
        return super(SaleOrder, self).write(vals)

    def _prepare_subscription_data(self, template):
        values = super(SaleOrder, self)._prepare_subscription_data(template)
        if 'current_order' in self._context:
            values['ns_special_billing_instruction'] = self.ns_special_billing_instruction
        return values

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['ns_special_billing_instruction'] = self.ns_special_billing_instruction
        return res

    def _action_confirm(self):
        super(SaleOrder, self)._action_confirm()

        return True
    
    # If Special Billing Instructions is enabled, this quotation must be confirmed by one in each of the groups
    def action_preconfirm(self):
        if self.ns_special_billing_instruction:
            if self.ns_confirmed == 0:
                if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                    self.ns_confirmed += 1
                if self.env.user.has_group('account.group_account_manager'):
                    self.ns_confirmed += 2
                if self.ns_confirmed == 0:
                    raise AccessError('You do not have the permission to confirm this quotation!')
            elif self.ns_confirmed == 1:
                if self.env.user.has_group('account.group_account_manager'):
                    self.ns_confirmed += 2
                elif self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                    group = self.env.ref('account.group_account_manager')
                    if group == None or group == False:
                        raise MissingError('The group account.group_account_manager does not exist!')
                    else:
                        raise AccessError(f'"{group.full_name}" must also confirm this quotation')
            elif self.ns_confirmed == 2:
                if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                    self.ns_confirmed += 1
                elif self.env.user.has_group('account.group_account_manager'):
                    group = self.env.ref('nrs_de_permission_sales_team.nrs_group_sale_support')
                    if group == None or group == False:
                        raise MissingError('The group nrs_de_permission_sales_team.nrs_group_sale_support does not exist!')
                    else:
                        raise AccessError(f'"{group.full_name}" must also confirm this quotation')
                        
            if self.ns_confirmed == 3:
                self.action_confirm()
        else:
            if self.env.user.has_group('nrs_de_permission_sales_team.nrs_group_sale_support'):
                self.action_confirm()
            else:
                raise AccessError('You do not have the permission to confirm this quotation!')