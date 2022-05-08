from . import models

from odoo import api, SUPERUSER_ID

def _sale_order_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sale_orders = env['sale.order'].search([('state', '!=', 'draft')])
    for sale_order in sale_orders:
        sale_order.approval_state = sale_order.state
