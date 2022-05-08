from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta

class SaleSubscription(models.Model):
	_inherit = "sale.subscription"

	def _recurring_create_invoice(self, automatic=False):
		res = super(SaleSubscription, self)._recurring_create_invoice(automatic)
		for inv in res:
			message = _("This invoice has been created from the MRC: <a href=# data-oe-model=sale.subscription data-oe-id=%d>%s</a>") % (inv.ns_origin_mrc.id, inv.ns_origin_mrc.display_name)
			inv.message_post(body=message)
		return res




