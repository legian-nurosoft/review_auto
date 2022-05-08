# -*- coding: utf-8 -*-

import odoo
import logging
from odoo import http, _
from odoo.addons.web.controllers.main import Home, Binary, ensure_db
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_totp.controllers.home import Home as AuthTotpHome
from odoo.http import request, route
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AuthTotpHomeInhherit(AuthTotpHome):
    @http.route()
    def web_totp(self, redirect=None, **kwargs):
        response = super(AuthTotpHomeInhherit, self).web_totp(redirect, **kwargs)
        carousel = request.env['portal.carousel'].sudo().search([],order="sequence ASC")
        response.qcontext.update({'carousel': carousel})

        languages = request.env['res.lang'].sudo().get_available()
        response.qcontext.update({'languages': languages})

        return response


class Home(Home):
    @http.route()
    def web_login(self, *args, **kw):      
        
        response = super(Home, self).web_login(*args, **kw)
        carousel = request.env['portal.carousel'].sudo().search([],order="sequence ASC")
        response.qcontext.update({'carousel': carousel})

        languages = request.env['res.lang'].sudo().get_available()
        response.qcontext.update({'languages': languages})

        if 'error' in request.params and request.params.get('err_domain') == 'portal':
            response.qcontext.update({'error':  _('This domain cannot be used to acces ERP. please use correct domain to acces ERP!')})
        elif 'error' in request.params and request.params.get('err_domain') == 'erp':
            response.qcontext.update({'error':  _('This domain cannot be used to acces Portal. please use correct domain to acces Portal!')})

        return response

    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
            return http.local_redirect('/portal', query=request.params, keep_hash=True)
        return super(Home, self).index(*args, **kw)

    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            redirect = '/portal'
        return super(Home, self)._login_redirect(uid, redirect=redirect)

    @route(['/privacy-policy'], type='http', auth="public", website=True)
    def privacy_policy(self, **kw):
        link = request.env['nrs.external.link'].sudo().search([('nrs_type', '=', 'privacy_policies')], limit=1)
        data = {
            'url' : '',
            'company' : 'Digital Edge',
        }
        if link:
            data['url'] = link.nrs_url
        
        #chuanjun website
        # base_url = request.httprequest.host
        # if (base_url == "nervous-penguin-39.telebit.io"):
        host_url = request.httprequest.host_url
        chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
        if chuanjun_domain and chuanjun_domain in host_url:
            data['company'] = "Chuanjun Information Technology (Shanghai) Limited"
        return request.render("nrs_de_portal.de_privacy_policy", data)
    
    @route(['/customer-portal-user-guide'], type='http', auth="public", website=True)
    def render_user_guide(self, **kw):
        page = kw.get('page', '1')
        data  = {
            'pdf_source': '/nrs_de_portal/static/src/pdf/customer_user_guide_1_0.pdf#toolbar=0&page=' + page
        }
        return request.render("nrs_de_portal.de_customer_portal_user_guide", data)

    @route(['/contact-us'], type='http', auth="public", website=True)
    def contact_us(self, **kw):
        return 'Contact Us'

class BinaryInherit(Binary):

    @http.route(['/portal/partner_image/<int:rec_id>'], type='http', auth="public")
    def content_image_partner_portal(self, rec_id, field='image_128', model='res.partner', **kwargs):
        # other kwargs are ignored on purpose
        return self._content_image_portal(id=rec_id, model='res.partner', field=field,
            placeholder='user_placeholder.jpg')

    def _content_image_portal(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename_field='name', unique=None, filename=None, mimetype=None,
                       download=None, width=0, height=0, crop=False, quality=0, access_token=None,
                       placeholder=None, **kwargs):
        status, headers, image_base64 = request.env['ir.http'].sudo().binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype='image/png', access_token=access_token)

        return Binary._content_image_get_response(
            status, headers, image_base64, model=model, id=id, field=field, download=download,
            width=width, height=height, crop=crop, quality=quality,
            placeholder=placeholder)

class AuthSignupHomeInherit(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    # template = request.env.ref('nrs_de_portal.mail_template_user_signup_account_created_internal', raise_if_not_found=False)
                    
                    #chuanjun company name
                    # base_url = request.httprequest.host
                    # company = "DIGITAL EDGE DC"
                    # if (base_url == "nervous-penguin-39.telebit.io"):                    
                    host_url = request.httprequest.host_url
                    chuanjun_domain = request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url')
                    if chuanjun_domain and chuanjun_domain in host_url:
                        company_name = "CHUANJUN"
                    else:
                        company_name = "DIGITAL EDGE DC"
                    # if user_sudo and template:
                    if user_sudo:
                        # template.sudo().with_context(company_name=company_name).send_mail(user_sudo.id, force_send=True)
                        user_partner = user_sudo.partner_id
                        if user_partner:
                            user_partner.sudo().write({'nrs_privacy_policy_agreement': True})
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
        
    # @http.route()
    # def web_auth_reset_password(self, *args, **kw):
        
    #     response = super(AuthSignupHomeInherit, self).web_auth_reset_password(*args, **kw)
    #     carousel = request.env['portal.carousel'].sudo().search([],order="sequence ASC")
    #     response.qcontext.update({'carousel': carousel})

    #     languages = request.env['res.lang'].sudo().get_available()
    #     response.qcontext.update({'languages': languages})

    #     return response

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        qcontext['vercode'] = kw.get('vercode', False)

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _("An email has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def do_signup(self, qcontext):
        user = request.env['res.users'].sudo().search([('login','=',qcontext.get('login',''))],limit=1)
        
        if user:
            if user.partner_id.nrs_reset_password_code != qcontext.get('vercode',False) and user.state == 'active':
                raise UserError(_("Verification code is invalid."))

        values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))

        base_url = request.httprequest.base_url  
        host_url = request.httprequest.host_url
        if "reset_password" in base_url:
            if user:
                if user.has_group('base.group_user'):
                    template = request.env.ref('nrs_de_portal.reset_password_success_internal', raise_if_not_found=False)                    
                    host_url = "https://boss.digitaledgedc.com/reset_password"
                elif user.has_group('base.group_portal'):
                    template = request.env.ref('nrs_de_portal.reset_password_success_portal', raise_if_not_found=False)                    
                    host_url = "https://portal.digitaledgedc.com"

                text_company_name = "Digital Edge"
                image_mail_logo = request.env['ir.config_parameter'].sudo().get_param('web.base_url', '') + "/nrs_de_portal/static/src/img/mail_logo.png"
                reset_password_link = "https://portal.digitaledgedc.com/reset_password"
                partner = user.partner_id
                if partner:
                    if partner.nrs_company_type == "person":
                        company = request.env['res.company'].sudo().search([('name', 'ilike', 'chuanjun'), ('company_registry', '=', '15000000202103090055')], limit=1)
                        company_partner = False
                        if company: 
                            company_partner = company.partner_id
                        if company_partner:  
                            if partner.parent_id == company_partner:
                                text_company_name = "Chuanjun"
                                image_mail_logo = request.env['ir.config_parameter'].sudo().get_param('web.base_url', '') + "/nrs_de_portal/static/src/img/mail_logo_chuanjun.png"
                                reset_password_link = "https://" + request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url', "portal.digitaledgedc.com/reset_password")
                                host_url = "https://" + request.env['ir.config_parameter'].sudo().get_param('nrs_de_portal.ns_chuanjun_portal_url', "portal.digitaledgedc.com/reset_password")
                
                template.sudo().with_context(host_url=host_url, text_company_name=text_company_name, image_mail_logo=image_mail_logo, reset_password_link=reset_password_link).send_mail(user.id, force_send=True)

        return super(AuthSignupHomeInherit, self).do_signup(qcontext)

        