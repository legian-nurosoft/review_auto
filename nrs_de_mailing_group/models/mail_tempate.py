# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, tools
# from odoo.exceptions import UserError

import logging
logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    ns_mailing_group = fields.Many2many(
        'ns.mailing.group', string='Mailing Group')

    @api.onchange('ns_mailing_group')
    def set_emails_to(self):
        receipt_list = []

        if self.ns_mailing_group:
            for i in self.ns_mailing_group.ns_team_leader_id:
                if i.login not in receipt_list:
                    receipt_list.append(i.login)

            for i in self.ns_mailing_group.ns_member_ids:
                if i.login not in receipt_list:
                    receipt_list.append(i.login)


        self.email_to = ';'.join(map(lambda x: x, receipt_list))

            # logger.info(
            #     '=================value emaiil %s ===============================' % self.ns_mailing_group.ns_member_ids.login)