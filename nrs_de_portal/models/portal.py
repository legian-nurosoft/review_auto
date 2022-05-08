# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PortalCarousel(models.Model):
    _name = 'portal.carousel'

    name = fields.Char()
    content = fields.Text()
    sequence = fields.Integer()


class FaqGroup(models.Model):
    _name = 'nrs.faq.group'
    _order = 'nrs_sequence asc'        
    _rec_name = 'nrs_name'

    nrs_name = fields.Char('Group Name')
    nrs_sequence = fields.Integer('Sequence',default=1)
    nrs_faq_ids = fields.One2many('nrs.faq','nrs_faq_group_id')


class Faq(models.Model):
    _name = 'nrs.faq'
    _order = 'nrs_sequence asc'
    _rec_name = 'nrs_title'

    nrs_title = fields.Char('Title')
    nrs_body = fields.Char('Body')
    nrs_sequence = fields.Integer('Sequence',default=1)
    nrs_faq_group_id = fields.Many2one('nrs.faq.group', 'Group')


class Documents(models.Model):
    _name = 'nrs.documents'
    _order = 'nrs_sequence asc'
    _rec_name = 'nrs_title'

    nrs_title = fields.Char('Title')
    nrs_description = fields.Char('Description')
    nrs_body = fields.Char('Body')
    nrs_download_link = fields.Char('Download Link')
    nrs_published_date = fields.Date('Published Date')
    nrs_type = fields.Selection([
            ('policies', 'Policies'),
            ('user_guide', 'User Guide')
        ], string='Type', default='policies')
    nrs_sequence = fields.Integer('Sequence',default=1)

class ExternalLink(models.Model):
    _name = 'nrs.external.link'
    _order = 'nrs_name asc'
    _rec_name = 'nrs_name'

    nrs_name = fields.Char('Name')
    nrs_url = fields.Char('URL')
    nrs_type = fields.Selection([
            ('privacy_policies', 'Privacy Policies'),
            ('order_agreement', 'Order Agreement')
        ], string='Link Type', default='privacy_policies')


class Message(models.Model):
    _inherit = 'mail.message'

    body = fields.Html('Contents', default='', sanitize_style=True)
    