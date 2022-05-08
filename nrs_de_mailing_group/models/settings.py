from odoo import models, fields, api
import logging

class SettingMailingGroup(models.Model):
	_name = 'ns.mailing.group'
	_rec_name = 'ns_name'
	# _inherit = ['mail.thread']
	_description = "Mailing Team"
	# _check_company_auto = True
	
	# def _get_default_team_id(self, user_id=None, domain=None):
	# 	ns_team_leader_id = ns_team_leader_id or self.env.uid
	# 	user_mailing_group_id = self.env['res.users'].browse(ns_team_leader_id).sale_team_id.id
	# 	# Avoid searching on member_ids (+1 query) when we may have the user salesteam already in cache.
	# 	team = self.env['ns.mailing.group'].search([
	# 		('user_id', '=', ns_team_leader_id), ('id', '=', user_mailing_group_id),
	# 		], limit=1)
	# 	if not team and 'default_team_id' in self.env.context:
	# 		team = self.env['ns.mailing.group'].browse(self.env.context.get('default_team_id'))
		
	# 	return team or self.env['ns.mailing.group'].search(domain or [], limit=1)

	ns_name = fields.Char('Name', required=True,  translate=True)
	ns_team_leader_id = fields.Many2one('res.users', string='Team Leader')
    # memberships
	ns_member_ids = fields.Many2many(
		'res.users', 'ns_mailing_group_id', string='Channel Members',
		help="Add members to automatically assign their documents to this sales team. You can only be member of one team.")

