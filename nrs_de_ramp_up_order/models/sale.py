from odoo import fields, models, api, exceptions, _
import calendar
from datetime import timedelta, datetime
from odoo.exceptions import UserError
from odoo.tools import format_date, float_compare
from odoo.tools.float_utils import float_is_zero
import uuid
import logging
_logger = logging.getLogger(__name__)


INTERVAL_FACTOR = {
    'daily': 30.0,
    'weekly': 30.0 / 7.0,
    'monthly': 1.0,
    'yearly': 1.0 / 12.0,
}

PERIODS = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	ns_is_ramp_up = fields.Boolean('Ramp Up?', default=False, copy=False)
	ns_ramp_ups = fields.One2many('ns.ramp.ups', 'ns_sale_id', copy=False, string="Ramp Up")
	def_name_ramp = fields.Char(compute="get_ramp_id")

	@api.onchange('order_line','order_line.product_id','order_line.product_uom_qty','order_line.discount','order_line.price_unit', 'order_line.tax_id')
	def update_ramp_up_line(self):
		for line in self.order_line:
			if not line.display_type:	
				for ramp_up in self.ns_ramp_ups:
					is_exist = False
					for ramp_up_line in ramp_up.ns_ramp_up_lines:
						if ramp_up_line.ns_sale_line_id.id == line._origin.id or ramp_up_line.ns_sale_line_unique_id == line.ns_unique_id:
							is_exist = True
							self.update({
								'ns_ramp_ups': [(1, ramp_up._origin.id, {
										'ns_ramp_up_lines': [(1, ramp_up_line._origin.id, {
											'display_name': line.product_id.name,
											'ns_sale_qty': line.product_uom_qty,
											'ns_product_id': line.product_id.id,
											'ns_discount': line.discount,
											'ns_price_unit': line.price_unit,										
											'ns_remarks': line.x_studio_remarks,
											'ns_tax_id': line.tax_id if line.tax_id else False,
											'ns_subtotal': line.price_subtotal,
											'ns_price_total': line.price_total
										})]
									})]
							})

					if not is_exist:
						self.update({
								'ns_ramp_ups': [(1, ramp_up._origin.id, {
										'ns_ramp_up_lines': [(0, 0, {
											'ns_sale_line_unique_id': line.ns_unique_id,
											'name': line.name,
											'display_name': line.product_id.name,
											'ns_sale_qty': line.product_uom_qty,
											'ns_product_id': line.product_id.id,
											'ns_qty': 0,
											'ns_product_id': line.product_id.id,
											'ns_discount': line.discount,
											'ns_price_unit': line.price_unit,										
											'ns_remarks': line.x_studio_remarks,
											'ns_tax_id': line.tax_id if line.tax_id else False,
											'ns_subtotal': line.price_subtotal,
											'ns_price_total': line.price_total
										})]
									})]
							})
	
	@api.onchange('ns_ramp_ups')
	def get_ramp_id(self):		
		ramp_ups = self.env['ns.ramp.ups']
		ramp_ups.automation_name_ramp_ups(self.ns_ramp_ups)
		for rec in self:
			rec.def_name_ramp = len(rec.ns_ramp_ups)
			
		# return {}


	@api.depends('ns_ramp_ups')
	def dep_get_ramp_id(self):
		ramp_ups = self.env['ns.ramp.ups']
		ramp_ups.automation_name_ramp_ups(self.ns_ramp_ups)

	def send_notification_to_manager(self):
		return True

	def append_line(self, ramp_up_line):
		line = ramp_up_line.ns_sale_line_id
		if not line.display_type and ramp_up_line.ns_qty > 0:
			return (0,0,{
				'sale_line_id': line.id,
				'product_id': line.product_id.id,
				'name': line.name,
				'product_uom_qty': ramp_up_line.ns_qty,
				'price_unit': line.price_unit,
				'tax_id': [(6,0,line.tax_id.ids)],
				'discount': line.discount
			})
		else:
			return []

	def create_sale_ramp_ups(self, ramp_up_to_execute, execute_now=False):
		wizard = self.env['sale.ramp.ups'].create({
			'sale_id': self.id,
			'ramp_up_to_execute': ramp_up_to_execute.id
		})
		order_line = [(5,0,0)]
		for ramp_up_line in ramp_up_to_execute.ns_ramp_up_lines:
			data_order_line = self.append_line(ramp_up_line)
			if data_order_line:
				order_line.append(data_order_line)
		wizard.order_line = order_line
		if execute_now:
			wizard.confirm_ramp_ups()

		return {
			'name': 'Sale Order : '+self.name,
			'view_mode': 'form',
			'view_id': self.env.ref('nrs_de_ramp_up_order.sale_ramp_ups_form').id,
			'view_type': 'form',
			'res_model': 'sale.ramp.ups',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'target': 'new'
		}

	def create_task_ramp_ups(self):
		for rec in self.ns_ramp_ups:
			rec._timesheet_service_generation()

	@api.constrains('ns_ramp_ups')
	def check_qty_ramp_up_and_order_line(self):
		if self.ns_is_ramp_up and self.ns_ramp_ups:
			for line in self.order_line:
				qty_ramp_up_per_order_line = sum(self.ns_ramp_ups.mapped('ns_ramp_up_lines').filtered(lambda l: l.ns_sale_line_id == line).mapped('ns_qty'))
				if qty_ramp_up_per_order_line > line.product_uom_qty:
					raise UserError("Total Qty Product '%s' in Order Lines is %s and in Ramp Up is %s. Please Check Table Ramp Up First!" % (line.product_id.display_name, line.product_uom_qty, qty_ramp_up_per_order_line))

	def action_confirm(self):
		for line in self.order_line:
			if not line.ns_has_reserved_space_or_breaker and not line.order_id.ns_is_change_order:
				if line.product_template_id.ns_capacity_assignation == 'space_id':
					raise exceptions.ValidationError(_('Please reserve Space ID for one or more of your order lines'))

				elif line.product_template_id.ns_capacity_assignation == 'breaker_id':
					raise exceptions.ValidationError(_('Please reserve Breaker ID for one or more of your order lines'))
				                
				elif line.product_template_id.ns_capacity_assignation == 'patch_panel_id':
					raise exceptions.ValidationError(_('Please reserve Patch Panel ID for one or more of your order lines'))

				elif line.product_template_id.ns_capacity_assignation == 'port_id':
					raise exceptions.ValidationError(_('Please reserve Port ID for one or more of your order lines'))
			# capacity is set and need to check the valid date
			else:
				if line.product_template_id.ns_capacity_assignation == 'space_id':
					capacity = self.env['ns.ns_space'].search([('ns_sale_order_line_id', '=', line.id)])
					for cap in capacity:
						if fields.Date().today() > cap.ns_reserve_date_until:
							raise exceptions.ValidationError(_('Reservation date for this record %s has expired or invalid. Please check the assigned capacity and assign a new capacity' % (cap.ns_name)))
				elif line.product_template_id.ns_capacity_assignation == 'breaker_id':
					capacity = self.env['ns.ns_breaker'].search([('ns_sale_order_line_id', '=', line.id)])
					for cap in capacity:
						if fields.Date().today() > cap.ns_reserve_date_until:
							raise exceptions.ValidationError(_('Reservation date for this record %s has expired or invalid. Please check the assigned capacity and assign a new capacity' % (cap.ns_name)))
				elif line.product_template_id.ns_capacity_assignation == 'patch_panel_id':
					capacity = self.env['ns.ns_patchpanel'].search([('ns_sale_order_line_id', '=', line.id)])
					for cap in capacity:
						if fields.Date().today() > cap.ns_reserve_date_until:
							raise exceptions.ValidationError(_('Reservation date for this record %s has expired or invalid. Please check the assigned capacity and assign a new capacity' % (cap.ns_name)))
				elif line.product_template_id.ns_capacity_assignation == 'port_id':
					capacity = self.env['ns.ns_ports'].search([('ns_sale_order_line_id', '=', line.id)])
					for cap in capacity:
						if fields.Date().today() > cap.ns_reserve_date_until:
							raise exceptions.ValidationError(_('Reservation date for this record %s has expired or invalid. Please check the assigned capacity and assign a new capacity' % (cap.ns_name)))

		self.check_qty_ramp_up_and_order_line()
		ctx = self._context
		if self.ns_is_ramp_up and self.ns_ramp_ups and not ctx.get('from_wizard_sale_ramp_ups',False):
			for ramp in self.ns_ramp_ups:
				self.create_sale_ramp_ups(ramp, execute_now= True)
			self.create_task_ramp_ups()
			return
		if not self.ns_is_ramp_up and not self.ns_ramp_ups:
			self = self.with_context(non_ramp_up_sale_id=self)
		res = super(SaleOrder, self).action_confirm()
		crm = self.env['sale.subscription'].search([('x_studio_original_sales_order', '=', self.id)])
		return res


	def cancel_another_quotation(self):
		another_quotations = self.search([
			('opportunity_id','=',self.opportunity_id.id),
			('id','!=',self.id),
			('state','not in',['reject','cancel','sale','done']),
		])
		another_quotations.action_cancel()

	def update_data_crm_from_sale(self):
		if self.opportunity_id:
			crm = self.opportunity_id
			crm.lead_product_ids.unlink()
			crm.ramp_ups.unlink()
			for sale_line in self.order_line:
				if not sale_line.display_type:
					crm.lead_product_ids = [(0,0,{
						'product_id': sale_line.product_id.id,
						'name': sale_line.name,
						'qty': sale_line.product_uom_qty,
						'product_uom': sale_line.product_uom.id,
						'price_unit': sale_line.price_unit,
						'tax_id': [(6,0,sale_line.tax_id.ids)]
					})]
				else:
					crm.lead_product_ids = [(0,0,{
						'name': sale_line.name,
						'display_type': sale_line.display_type
					})]
			ramp_ups = self.env['ns.ramp.ups']
			for sale_ramp_up in self.ns_ramp_ups:
				ramp_up_lines = []
				for ramp_up_line in sale_ramp_up.ns_ramp_up_lines:
					index_crm_line_id = self.order_line.ids.index(ramp_up_line.ns_sale_line_id.id)
					if not ramp_up_line.display_type:
						ramp_up_lines.append((0,0,{
							'name': ramp_up_line.name,
							'crm_line_id': crm.lead_product_ids[index_crm_line_id].id,
							'crm_line_qty': ramp_up_line.ns_sale_qty,
							'product_id': ramp_up_line.ns_product_id.id,
							'qty': ramp_up_line.ns_qty
						}))
					else:
						ramp_up_lines.append((0,0,{
							'name': ramp_up_line.name,
							'crm_line_id': crm.lead_product_ids[index_crm_line_id].id,
							'display_type': ramp_up_line.display_type
						}))
				ramp_ups.create({
					'crm_id': crm.id,
					'name': sale_ramp_up.name,
					'mrc_qty': sale_ramp_up.mrc_qty,
					'nrc_qty': sale_ramp_up.nrc_qty,
					'start_date': sale_ramp_up.start_date,
					'ramp_up_lines': ramp_up_lines
				})
			crm.mrc_revenue = self.total_mrc
			crm.nrc_revenue = self.total_nrc

	def create_subscriptions(self):
		ctx = self._context
		if ctx.get('without_write_sale_line',False):
			ramp_up = ctx.get('ramp_up', False)
			res = []
			for order in self:
				to_create = self._split_subscription_lines()
				for template in to_create:
					values = order._prepare_subscription_data(template)
					values['recurring_invoice_line_ids'] = to_create[template]._prepare_subscription_line_data()
					values['ns_nrc_line_ids'] = (order.order_line - to_create[template])._prepare_nrc_line_data()
					values['x_studio_original_sales_order'] = order.id
					values['code'] = "%s-R%s"%(order.name, ramp_up.name[5:]) 
					values['ns_ramp_up'] = ramp_up.id
					subscription = self.env['sale.subscription'].sudo().create(values)
					subscription.onchange_date_start()
					res.append(subscription.id)
					subscription.message_post_with_view(
						'mail.message_origin_link', values={'self': subscription, 'origin': order},
						subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
					)
					#create Change For MRC
					self.env['sale.subscription.log'].sudo().create({
						'subscription_id': subscription.id,
						'event_date': fields.Date.context_today(self),
						'event_type': '0_creation',
						'amount_signed': subscription.recurring_monthly,
						'recurring_monthly': subscription.recurring_monthly,
						'currency_id': subscription.currency_id.id,
						'category': subscription.stage_category,
						'user_id': order.user_id.id,
						'team_id': order.team_id.id,
					})
					#create Change For NRC
					self.env['sale.subscription.log'].sudo().create({
						'subscription_id': subscription.id,
						'event_date': fields.Date.context_today(self),
						'event_type': '0_creation',
						'amount_signed': subscription.ns_non_recurring_total,
						'recurring_monthly': subscription.ns_non_recurring_total,
						'currency_id': subscription.currency_id.id,
						'category': subscription.stage_category,
						'user_id': order.user_id.id,
						'team_id': order.team_id.id,
						'ns_is_nrc': True,
					})

			return res
		else:
			res = super(SaleOrder, self).create_subscriptions()
			ramp_up = ctx.get('ramp_up', False)
			for rec in res:
				subs = self.env['sale.subscription'].browse(rec)
				if ramp_up:
					subs.code = "%s-R%s"%(subs.x_studio_original_sales_order.name, ramp_up.name[5:])
					subs.ns_ramp_up = ramp_up
				lines = subs.x_studio_original_sales_order.order_line.filtered(lambda x: not x.product_id.recurring_invoice)
				subs.ns_nrc_line_ids = lines._prepare_nrc_line_data()					
				self.env['sale.subscription.log'].sudo().create({
					'subscription_id': subs.id,
					'event_date': fields.Date.context_today(self),
					'event_type': '0_creation',
					'amount_signed': subs.ns_non_recurring_total,
					'recurring_monthly': subs.ns_non_recurring_total,
					'currency_id': subs.currency_id.id,
					'category': subs.stage_category,
					'user_id': subs.x_studio_original_sales_order.user_id.id,
					'team_id': subs.x_studio_original_sales_order.team_id.id,
					'ns_is_nrc': True,
				})
			return res

	def _split_subscription_lines(self):
		ctx = self._context
		if isinstance(ctx.get('list_lines_to_subscribe',False), dict):
			self.ensure_one()
			res = dict()
			lines_to_sub = ctx['list_lines_to_subscribe']
			new_sub_lines = self.env['sale.order.line']
			for line in lines_to_sub:
				if lines_to_sub[line] > 0:
					new_sub_lines += line
			templates = new_sub_lines.mapped('product_id').mapped('subscription_template_id')
			for template in templates:
				lines = new_sub_lines.filtered(lambda l: l.product_id.subscription_template_id == template)
				res[template] = lines
			return res
		else:
			return super(SaleOrder, self)._split_subscription_lines()

	def _compute_subscription_count(self):
		"""Compute the number of distinct subscriptions linked to the order."""
		for order in self:
			if order.ns_is_ramp_up:
				sub_count = len(self.env['ns.ramp.ups'].read_group([('ns_sale_id', '=', order.id), ('ns_subscription', '!=', False)],
														['ns_subscription'], ['ns_subscription']))
			else:
				sub_count = len(self.env['sale.order.line'].read_group([('order_id', '=', order.id), ('subscription_id', '!=', False)],
														['subscription_id'], ['subscription_id']))

			order.subscription_count = sub_count

	def action_open_subscriptions(self):
		"""Display the linked subscription and adapt the view to the number of records to display."""
		self.ensure_one()

		# subscriptions = self.order_line.mapped('subscription_id')
		if self.ns_is_ramp_up:
			subscriptions = self.ns_ramp_ups.mapped('ns_subscription')
		else:
			subscriptions = self.order_line.mapped('subscription_id')
		action = self.env["ir.actions.actions"]._for_xml_id("sale_subscription.sale_subscription_action")
		if len(subscriptions) > 1:
			action['domain'] = [('id', 'in', subscriptions.ids)]
		elif len(subscriptions) == 1:
			form_view = [(self.env.ref('sale_subscription.sale_subscription_view_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = subscriptions.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		action['context'] = dict(self._context, create=False)
		return action

	def update_existing_subscriptions(self):
		res = super(SaleOrder, self).update_existing_subscriptions()
		product = self._context.get('product')
		for order in self:
			subscriptions = order.order_line.mapped('subscription_id').sudo()
			for subs in subscriptions:
				nrc_lines = order.order_line.filtered(lambda l: l.subscription_id == subs and not l.product_id.recurring_invoice)
				if product:
					if nrc_lines.product_id.id == product['product_id']:
						line_values = nrc_lines.with_context(product=product)._update_nrc_line_data(subs)
						subs.write({'ns_nrc_line_ids': line_values})
						#change the adjusted status of the task
						order_line = self.env['sale.order.line'].browse(product['order_line_id'])
						order_line.ns_is_adjusted = True
		return res

	def _create_invoices(self, grouped=False, final=False, date=None):
		moves = super(SaleOrder, self)._create_invoices(grouped, final, date)

		for move in moves:
			move_lines = move.invoice_line_ids
			mrc_lines = []
			nrc_lines = []
			ignored_lines = []
			sequence = 0
			in_section = False

			for line in move_lines:
				if not in_section:
					if 'display_type' in line and line['display_type'] == 'line_section':
						ignored_lines.append(line)
						in_section = True
					elif line.product_id.recurring_invoice:
						mrc_lines.append(line)
					else:
						nrc_lines.append(line)
				else:
					ignored_lines.append(line)
				
			
			if len(nrc_lines) != 0:
				move.write({'invoice_line_ids': [
					(0, 0, {'sequence': sequence, 'name': 'Non Recurring Charge (NRC)', 'display_type': 'line_section'})
				]})
				sequence += 1
				
				for line in nrc_lines:
					line.write({'sequence': sequence})
					sequence += 1

			if len(mrc_lines) != 0:
				move.write({'invoice_line_ids': [
					(0, 0, {'sequence': sequence, 'name': 'Monthly Recurring Charge (MRC)', 'display_type': 'line_section'})
				]})
				sequence += 1

				for line in mrc_lines:
					line.write({'sequence': sequence})
					sequence += 1

			for line in ignored_lines:
				line.write({'sequence': sequence})
				sequence += 1

			return moves


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	def _get_unique_id(self):
		return uuid.uuid4().hex

	ns_project_task_id = fields.Many2many('project.task', string='Task', compute='_compute_project_task')
	ns_unique_id = fields.Char('Unique ID', default=_get_unique_id)

	def _compute_project_task(self):
		for rec in self:
			rec.ns_project_task_id = False
			related_tasks = self.env['project.task'].search([('sale_line_id','=',rec.id), ('parent_id','=',False)])
			for related_task in related_tasks:
				rec.ns_project_task_id += related_task.x_studio_sub_tasks

	def _prepare_subscription_line_data(self):
		ctx = self._context
		if isinstance(ctx.get('list_lines_to_subscribe',False), dict):
			lines_to_sub = ctx['list_lines_to_subscribe']
			values = list()
			for line in self:
				if not line.display_type:
					qty = lines_to_sub.get(line,0)
					if qty > 0:
						values.append((0, False, {
							# 'sale_line_id': line.id,
							'product_id': line.product_id.id,
							'name': line.name,
							'quantity': qty,
							'uom_id': line.product_uom.id,
							'price_unit': line.price_unit,
							'ns_product_attribute_value': line.ns_product_attribute_value.id,
							'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
						}))
			return values
		else:
			values = list()
			for line in self:
				if not line.display_type:
					values.append((0, False, {
						# 'sale_line_id': line.id,
						'product_id': line.product_id.id,
						'name': line.name,
						'quantity': line.product_uom_qty,
						'uom_id': line.product_uom.id,
						'price_unit': line.price_unit,
						'ns_product_attribute_value': line.ns_product_attribute_value.id,
						'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
					}))
			return values

	def _prepare_nrc_line_data(self):
		ctx = self._context
		if isinstance(ctx.get('list_lines_nrc',False), dict):
			lines_to_sub = ctx['list_lines_nrc']
			values = list()
			for line in self:
				if not line.display_type:
					qty = lines_to_sub.get(line,0)
					if qty > 0:
						values.append((0, False, {
							# 'sale_line_id': line.id,
							'ns_is_nrc': True,
							'product_id': line.product_id.id,
							'name': line.name,
							'quantity': qty,
							'uom_id': line.product_uom.id,
							'price_unit': line.price_unit,
							'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
						}))
			return values
		else:
			values = list()
			for line in self:
				if not line.display_type:
					values.append((0, False, {
						# 'sale_line_id': line.id,
						'ns_is_nrc': True,
						'product_id': line.product_id.id,
						'name': line.name,
						'quantity': line.product_uom_qty,
						'uom_id': line.product_uom.id,
						'price_unit': line.price_unit,
						'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
					}))
			return values

	def _update_subscription_line_data(self, subscription):
		ctx = self._context
		if isinstance(ctx.get('list_lines_to_subscribe',False), dict):
			lines_to_sub = ctx['list_lines_to_subscribe']
			values = list()
			dict_changes = dict()
			for line in self:
				qty = lines_to_sub.get(line,0)
				if qty > 0:
					sub_line = subscription.recurring_invoice_line_ids.filtered(
						lambda l: (l.product_id, l.uom_id, l.price_unit) == (line.product_id, line.product_uom, line.price_unit)
					)
					if sub_line:
						if len(sub_line) > 1:
							sub_line[0].copy({'name': line.display_name, 'quantity': qty})
						else:
							dict_changes.setdefault(sub_line.id, sub_line.quantity)
							dict_changes[sub_line.id] += qty
					else:
						values.append(line._prepare_subscription_line_data()[0])

			values += [(1, sub_id, {'quantity': dict_changes[sub_id],}) for sub_id in dict_changes]
			return values
		else:
			return super(SaleOrderLine, self)._update_subscription_line_data(subscription)

	def _update_nrc_line_data(self, subscription):
		ctx = self._context
		product = self._context.get('product')
		if isinstance(ctx.get('list_lines_nrc',False), dict):
			lines_to_sub = ctx['list_lines_nrc']
			values = list()
			dict_changes = dict()
			for line in self:
				qty = lines_to_sub.get(line,0)
				if qty > 0:
					sub_line = subscription.ns_nrc_line_ids.filtered(
						lambda l: (l.product_id, l.uom_id, l.price_unit) == (line.product_id, line.product_uom, line.price_unit)
					)
					if sub_line:
						if len(sub_line) > 1:
							sub_line[0].copy({'name': line.display_name, 'quantity': qty})
						else:
							dict_changes.setdefault(sub_line.id, sub_line.quantity)
							dict_changes[sub_line.id] += qty
					else:
						values.append(line._prepare_nrc_line_data()[0])

			values += [(1, sub_id, {'quantity': dict_changes[sub_id],}) for sub_id in dict_changes]
			return values
		else:
			values = list()
			dict_changes = dict()
			for line in self:
				if product:
					if line.product_id.id == product['product_id'] and not line.ns_is_adjusted:
						sub_line = subscription.ns_nrc_line_ids.filtered(
							lambda l: (l.product_id, l.uom_id, str(l.price_unit)) == (line.product_id, line.product_uom, 
										str(round(line.price_unit, 2)))
						)
						if sub_line:
							# We have already a subscription line, we need to modify the product quantity
							if len(sub_line) > 1:
								# we are in an ambiguous case
								# to avoid adding information to a random line, in that case we create a new line
								# we can simply duplicate an arbitrary line to that effect
								sub_line[0].copy({'name': line.display_name, 'quantity': line.product_uom_qty})
							else:
								dict_changes.setdefault(sub_line.id, sub_line.quantity)
								# upsell, we add the product to the existing quantity
								dict_changes[sub_line.id] += line.product_uom_qty
						else:
							# we create a new line in the subscription: (0, 0, values)
							nrc_line_data = line._prepare_nrc_line_data()
							values.append(nrc_line_data[0])

			values += [(1, sub_id, {'quantity': dict_changes[sub_id]}) for sub_id in dict_changes]
			return values


	def _timesheet_create_task(self, project):
		if not self.order_id.ns_is_ramp_up:
			return super()._timesheet_create_task(project)
		return False

	@api.model
	def create(self, values):
		res = super(SaleOrderLine, self).create(values)
		ramp_up_lines = self.env['ns.ramp.ups.line'].search([('ns_sale_line_unique_id','=',res.ns_unique_id)])
		
		for ramp_up_line in ramp_up_lines:
			ramp_up_line.write({'ns_sale_line_id': res.id})
		return res


class ProjectTask(models.Model):
	_inherit = 'project.task'

	x_studio_service_request_date = fields.Date("Service Request Date")
	ns_ramp_up_id = fields.Many2one('ns.ramp.ups','Ramp-Up Name', compute='_compute_related_ramp_up')

	def _compute_related_ramp_up(self):
		for rec in self:
			rec.ns_ramp_up_id = False
			if rec.parent_id:
				rec.ns_ramp_up_id = rec.parent_id.ns_ramp_up_id.id

			else:
				if rec.sale_order_id.ns_ramp_ups:
					for ramp_up in rec.sale_order_id.ns_ramp_ups:
						if ramp_up.ns_start_date == rec.x_studio_service_request_date:
							rec.ns_ramp_up_id = ramp_up.id


