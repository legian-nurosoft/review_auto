# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.http import request, route
import random
import logging
import werkzeug.urls

_logger = logging.getLogger(__name__)

def random_verification_code(lengths=6):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(lengths))

class Partner(models.Model):
    _inherit = 'res.partner'

    nrs_reset_password_code = fields.Char('Verification Code')
    nrs_default_url = fields.Char(compute="_compute_nrs_default_url")
    nrs_show_2fa_setting_message = fields.Boolean("show popup setting 2fa message ?", default=True)
    nrs_privacy_policy_agreement = fields.Boolean("is partner agree with privacy policy ?", default=False)


    def _compute_nrs_default_url(self):
        for rec in self:
            url = self.env['ir.config_parameter'].sudo().get_param('web.base_url', '')
            rec.nrs_default_url = url

    def signup_prepare(self, signup_type="signup", expiration=False):
        res = super(Partner, self).signup_prepare(signup_type=signup_type, expiration=expiration)
        for rec in self:
            rec.write({'nrs_reset_password_code': random_verification_code(6)})

        return res

    def _get_signup_url_for_action(self, url=None, action=None, view_type=None, menu_id=None, res_id=None, model=None):
        """ generate a signup url for the given partner ids and action, possibly overriding
            the url state components (menu_id, id, view_type) """

        res = dict.fromkeys(self.ids, False)
        for partner in self:
            base_url = partner.get_base_url()
            
            # when required, make sure the partner has a valid signup token
            if self.env.context.get('signup_valid') and not partner.user_ids:
                partner.sudo().signup_prepare()

            route = 'login'
            # the parameters to encode for the query
            query = dict(db=self.env.cr.dbname)
            signup_type = self.env.context.get('signup_force_type_in_url', partner.sudo().signup_type or '')
            if signup_type:
                route = 'reset_password' if signup_type == 'reset' else signup_type

            if partner.sudo().signup_token and signup_type:
                query['token'] = partner.sudo().signup_token
            elif partner.user_ids:
                query['login'] = partner.user_ids[0].login
            else:
                continue        # no signup token, no user, thus no signup url!

            if url:
                query['redirect'] = url
            else:
                fragment = dict()
                base = '/web#'
                if action == '/mail/view':
                    base = '/mail/view?'
                elif action:
                    fragment['action'] = action
                if view_type:
                    fragment['view_type'] = view_type
                if menu_id:
                    fragment['menu_id'] = menu_id
                if model:
                    fragment['model'] = model
                if res_id:
                    fragment['res_id'] = res_id

                if fragment:
                    query['redirect'] = base + werkzeug.urls.url_encode(fragment)

            user = partner.user_ids[0]
            portal_domain = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_portal_url', "portal.digitaledgedc.com")
            erp_domain = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_erp_url', "bss.digitaledgedc.com")
            chuanjun_portal_domain = self.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url', "portal.chuanjunnet.cn")

            if user:
                if user.has_group('base.group_user'):
                    if erp_domain and erp_domain != '':
                        base_url = "http://" + erp_domain + "/"
                elif user.has_group('base.group_portal'):
                    if portal_domain and portal_domain != '':
                        base_url = "http://" + portal_domain + "/"
                                                
                        company = self.env['res.company'].sudo().search([('name', 'ilike', 'chuanjun'), ('company_registry', '=', '15000000202103090055')], limit=1)
                        company_partner = False
                        if company: 
                            company_partner = company.partner_id
                        if company_partner:  
                            if partner.parent_id == company_partner:
                                base_url = "http://" + chuanjun_portal_domain + "/"

            url = "/web/%s?%s" % (route, werkzeug.urls.url_encode(query))
            if not self.env.context.get('relative_url'):
                url = werkzeug.urls.url_join(base_url, url)
            res[partner.id] = url

        return res

    @api.onchange('parent_id')
    def change_website_id(self):
        for rec in self:
            if rec.nrs_company_type == "person":
                parent = rec.parent_id
                if parent: 
                    parent_website =  parent.website_id
                    rec.website_id = parent_website         

    @api.model_create_multi
    def create(self, vals):
        records = super(Partner, self).create(vals)
        for record in records:
            if record.nrs_company_type == "person":
                parent = record.parent_id
                if parent: 
                    parent_website =  parent.website_id
                    record.website_id = parent_website
        return records


class User(models.Model):
    _inherit = 'res.users'

    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        _logger.info(">>>>>>>>>>>>>>>>>>>>> User::action_reset_password()")
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        if create_mode:
            self.mapped('partner_id').signup_prepare(signup_type="signup", expiration=expiration)
        else:
            self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        for user in self:
            # send email to users with their signup url
            template = False
            if create_mode:
                try:
                    if user.has_group('base.group_user'):
                        template = self.env.ref('nrs_de_portal.mail_template_user_signup_account_created_internal', raise_if_not_found=False)
                    elif user.has_group('base.group_portal'):
                        template = self.env.ref('nrs_de_portal.mail_template_user_signup_account_created_portal', raise_if_not_found=False)
                except ValueError:
                    pass
            if not template:
                if user.has_group('base.group_user'):
                    template = self.env.ref('nrs_de_portal.reset_password_email_internal')
                elif user.has_group('base.group_portal'):
                    template = self.env.ref('nrs_de_portal.reset_password_email_portal')
            assert template._name == 'mail.template'

            template_values = {
                'email_to': '${object.email|safe}',
                'email_cc': False,
                'auto_delete': True,
                'partner_to': False,
                'scheduled_date': False,
            }

            text_company_name = "Digital Edge"
            image_mail_logo = self.env['ir.config_parameter'].sudo().get_param('web.base_url', '') + "/nrs_de_portal/static/src/img/mail_logo.png" 
            partner = user.partner_id

            if partner:
                if partner.nrs_company_type == "person":
                    company = self.env['res.company'].sudo().search([('name', 'ilike', 'chuanjun'), ('company_registry', '=', '15000000202103090055')], limit=1)
                    company_partner = False
                    if company: 
                        company_partner = company.partner_id
                    if company_partner:  
                        if partner.parent_id == company_partner:
                            text_company_name = "Chuanjun"
                            image_mail_logo = self.env['ir.config_parameter'].sudo().get_param('web.base_url', '') + "/nrs_de_portal/static/src/img/mail_logo_chuanjun.png"
            
            company_name = "DIGITAL EDGE DC"       
            host_url = request.httprequest.host_url
            chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
            if chuanjun_domain and chuanjun_domain in host_url:
                company_name = "CHUANJUN"
            template.write(template_values)

            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.with_context(company_name=company_name, text_company_name=text_company_name, image_mail_logo=image_mail_logo).send_mail(user.id, force_send=force_send, raise_exception=True)


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def action_apply(self):
        self.ensure_one()
        self.user_ids.with_context({'nrs_skip_email':1, 'override_grant_portal': 1}).action_apply()
        return {'type': 'ir.actions.act_window_close'}

class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def _send_email(self):
        """ send notification email to a new portal user """
        print('portal_wizard__send_email')
        if not self.env.user.email:
            raise UserError(_('You must have an email address in your User Preferences to send emails.'))

        # determine subject and body in the portal user's language
        template = self.env.ref('nrs_de_portal.set_password_email')

        for wizard_line in self:
            lang = wizard_line.user_id.lang
            partner = wizard_line.user_id.partner_id
            company = "DIGITAL EDGE DC"

            host_url = request.httprequest.host_url
            chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
            if chuanjun_domain and chuanjun_domain in host_url:
                company_name = "CHUANJUN"

            portal_url = partner.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[partner.id]
            partner.signup_prepare()

            if template and 'nrs_skip_email' not in self._context:           
                template.with_context(dbname=self._cr.dbname, portal_url=portal_url, lang=lang, company_name=company_name).send_mail(wizard_line.id, force_send=True)
            else:
                _logger.warning("No email template found for sending email to the portal user")

        return True

    def action_apply(self):
        self.env['res.partner'].check_access_rights('write')
        """ From selected partners, add corresponding users to chosen portal group. It either granted
            existing user, or create new one (and add it to the group).
        """
        error_msg = self.get_error_messages()
        if error_msg:
            raise UserError("\n\n".join(error_msg))

        for wizard_user in self.sudo().with_context(active_test=False):

            group_portal = self.env.ref('base.group_portal')
            #Checking if the partner has a linked user
            user = wizard_user.partner_id.user_ids[0] if wizard_user.partner_id.user_ids else None
            # update partner email, if a new one was introduced
            if wizard_user.partner_id.email != wizard_user.email:
                wizard_user.partner_id.write({'email': wizard_user.email})
            # add portal group to relative user of selected partners
            if wizard_user.in_portal:
                user_portal = None
                # create a user if necessary, and make sure it is in the portal group
                if not user:
                    if wizard_user.partner_id.company_id:
                        company_id = wizard_user.partner_id.company_id.id
                    else:
                        company_id = self.env.company.id
                    user_portal = wizard_user.sudo().with_company(company_id)._create_user()
                else:
                    user_portal = user
                wizard_user.write({'user_id': user_portal.id})
                # generate pin code
                wizard_user.partner_id.write({'x_studio_pin_code': random_verification_code(6)})
                if not wizard_user.user_id.active or group_portal not in wizard_user.user_id.groups_id:
                    wizard_user.user_id.write({'active': True, 'groups_id': [(4, group_portal.id)]})
                    # prepare for the signup process
                    wizard_user.user_id.partner_id.signup_prepare()
                company_name = "DIGITAL EDGE DC"
                host_url = request.httprequest.host_url
                chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
                if chuanjun_domain and chuanjun_domain in host_url:
                    company_name = "CHUANJUN"
                wizard_user.with_context(active_test=True, company_name=company_name)._send_email()
                wizard_user.refresh()
                if 'override_grant_portal' in self._context:
                    user_portal.with_context({'create_user':1}).action_reset_password()
            else:
                _logger.info(">>>>>>> action_apply() -> wizard_user.in_portal false")
                # remove the user (if it exists) from the portal group
                if user and group_portal in user.groups_id:
                    # if user belongs to portal only, deactivate it
                    if len(user.groups_id) <= 1:
                        user.write({'groups_id': [(3, group_portal.id)], 'active': False})
                    else:
                        user.write({'groups_id': [(3, group_portal.id)]})


