from odoo import api, models, api, exceptions, fields, _
import datetime
from dateutil.relativedelta import relativedelta


class RampUps(models.Model):
	_name = 'ns.ramp.ups'
	_order = 'id'
	_description = 'Ramp Ups'

	ns_crm_id = fields.Many2one('crm.lead', 'CRM')
	ns_sale_id = fields.Many2one('sale.order', 'Sales Order')
	name = fields.Char(copy=False, translate=True)
	ns_mrc_qty = fields.Float('MRC Qty', copy=False, default=0, compute="get_qty_ramp_ups", store=True)
	ns_nrc_qty = fields.Float('NRC Qty', copy=False, default=0, compute="get_qty_ramp_ups", store=True)
	ns_start_date = fields.Date("Start Date", copy=False)
	ns_subscription = fields.Many2one('sale.subscription', 'Subscription', copy=False)
	ns_move_id = fields.Many2one('account.move', string='Invoice', copy=False)
	ns_ramp_up_lines = fields.One2many('ns.ramp.ups.line', 'ns_ramp_up_id', string='Products', copy=False)
	ns_project_id = fields.Many2one('project.project', string="Project", copy=False)
	ns_mrc_amount = fields.Float('MRC Amount', copy=False, default=0, compute="get_qty_ramp_ups")
	ns_nrc_amount = fields.Float('NRC Amount', copy=False, default=0, compute="get_qty_ramp_ups")
	ns_project_task_id = fields.Many2many('project.task', string='Task', compute='_compute_project_task')	

	def _compute_project_task(self):
		for rec in self:
			rec.ns_project_task_id = False
			related_task = self.env['project.task'].search([('sale_order_id','=',rec.ns_sale_id.id), ('x_studio_service_request_date','=',rec.ns_start_date), ('parent_id','=',False)])
			if related_task:
				rec.ns_project_task_id = related_task

	def automation_name_ramp_ups(self, ramp_ups):
		seq = 1
		name = 'Ramp-'
		for ramp_up in ramp_ups:
			if ramp_up._origin:
				ramp_up._origin.name = name + str(seq)
			ramp_up.name = name + str(seq)
			seq += 1
		print("DATA", ramp_ups)

		# return True

	@api.depends('ns_ramp_up_lines','ns_ramp_up_lines.ns_qty')
	def get_qty_ramp_ups(self):
		for ramp_up in self:
			mrc_qty = 0
			nrc_qty = 0
			mrc_amount = 0
			nrc_amount = 0
			for ramp_up_line in ramp_up.ns_ramp_up_lines:
				product_id = ramp_up_line.ns_product_id
				if product_id and product_id.recurring_invoice:
					mrc_qty += ramp_up_line.ns_qty
					mrc_amount += ramp_up_line.ns_subtotal
				elif product_id:
					nrc_qty += ramp_up_line.ns_qty
					nrc_amount += ramp_up_line.ns_subtotal
			ramp_up.ns_mrc_qty = mrc_qty
			ramp_up.ns_nrc_qty = nrc_qty
			ramp_up.ns_mrc_amount = mrc_amount
			ramp_up.ns_nrc_amount = nrc_amount

	# def prepare_value_project_ramp_up(self):
	# 	return {
	# 		'name' : (self.ns_sale_id.name or '') + ' - ' + (self.name.replace(' - ',' ') or ''),
	# 		'partner_id': self.ns_sale_id.partner_id.id,
	# 		# 'sale_id': self.ns_sale_id.id
	# 	}

	# def create_project_ramp_up(self):
	# 	return self.env['project.project'].sudo().with_context(ramp_up_project=self).create(self.prepare_value_project_ramp_up())


	def get_default_ramp_up_lines(self, result):
		default_ramp_up_lines = []
		if result.get('ns_sale_id',False):

			# ctx_default_order_line = sale.order_line 
			ctx_default_order_line = self._context.get('default_order_line',[])
			obj_id_line = []
			# for product_sale in ctx_default_order_line:
			# 	if not product_sale.display_type and product_sale.product_uom_qty > 0:
			dt = []
			for sale_line in ctx_default_order_line:
				if sale_line and sale_line[0] == 4:
					product_sale = self.env['sale.order.line'].browse(sale_line[1])
					if not product_sale.display_type and product_sale.product_uom_qty > 0:
						default_ramp_up_lines.append((0,0,{
							'name': product_sale.name,
							'display_name': product_sale.product_id.name,
							'ns_sale_line_id': product_sale.id,
							'ns_sale_qty': product_sale.product_uom_qty,
							'ns_product_id': product_sale.product_id.id,
							'ns_qty': 0,
							'ns_discount': product_sale.discount,
							'ns_price_unit': product_sale.price_unit,
							'ns_remarks': product_sale.x_studio_remarks,
							'ns_tax_id': product_sale.tax_id if product_sale.tax_id else False,
							'ns_subtotal': product_sale.price_subtotal,
							'ns_price_total': product_sale.price_total
						}))
		return default_ramp_up_lines

	@api.model
	def default_get(self, fields):
		sale = False
		if 'default_ns_sale_id' in self._context:
			fields.append('ns_sale_id')
			sale = self.env['sale.order'].browse(self._context.get('default_ns_sale_id', 0))
		result = super(RampUps, self).default_get(fields)
		if 'default_nsdate' in self._context and sale:
			if int(self._context['default_nsdate']) == 0:
				result['ns_start_date'] =  sale.x_studio_service_request_date
		default_ramp_up_lines = self.get_default_ramp_up_lines(result)
		if default_ramp_up_lines:
			result['ns_ramp_up_lines'] = default_ramp_up_lines
		return result

	def checking_creating_ramp_up(self):
		if not self.ns_ramp_up_lines:
			raise exceptions.UserError('Products harus terisi.')

	@api.model
	def create(self, vals):
		crm_ids = super(RampUps, self).create(vals)
		crm_ids.checking_creating_ramp_up()
		return crm_ids

	def write(self, vals):
		res = super(RampUps, self).write(vals)
		self.checking_creating_ramp_up()
		return res

	def popup_save(self):
		print("DO Nothing")


	def _timesheet_service_generation(self):
		""" For service lines, create the task or the project. If already exists, it simply links
			the existing one to the line.
			Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
			new project/task. This explains the searches on 'sale_line_id' on project/task. This also
			implied if so line of generated task has been modified, we may regenerate it.
		"""
		so_line_task_global_project = self.ns_sale_id.order_line.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project')
		so_line_new_project = self.ns_sale_id.order_line.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking in ['project_only', 'task_in_project'])

		# search so lines from SO of current so lines having their project generated, in order to check if the current one can
		# create its own project, or reuse the one of its order.
		map_so_project = {}
		# if so_line_new_project:
		# 	order_ids = self.mapped('order_id').ids
		# 	so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '=', False)])
		# 	map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
		# 	so_lines_with_project_templates = self.env['sale.order.line'].search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '!=', False)])
		# 	map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for sol in so_lines_with_project_templates}

		# search the global project of current SO lines, in which create their task
		map_sol_project = {}
		if so_line_task_global_project:
			map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in so_line_task_global_project}

		def _can_create_project(sol):
			if not sol.project_id:
				if sol.product_id.project_template_id:
					return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
				elif sol.order_id.id not in map_so_project:
					return True
			return False

		def _determine_project(so_line):
			"""Determine the project for this sale order line.
			Rules are different based on the service_tracking:

			- 'project_only': the project_id can only come from the sale order line itself
			- 'task_in_project': the project_id comes from the sale order line only if no project_id was configured
			  on the parent sale order"""

			if so_line.product_id.service_tracking == 'project_only':
				return so_line.project_id
			elif so_line.product_id.service_tracking == 'task_in_project':
				return so_line.order_id.project_id or so_line.project_id

			return False

		# task_global_project: create task in global project
		for ramp_up in self.ns_ramp_up_lines:
			so_line = ramp_up.ns_sale_line_id
			if map_sol_project.get(so_line.id) and ramp_up.ns_qty > 0:
				task = ramp_up._timesheet_create_task(project=map_sol_project[so_line.id])

class RampUpsLine(models.Model):
	_name = 'ns.ramp.ups.line'
	_order = 'ns_ramp_up_id, sequence, id'
	_description = 'Ramp Ups Line'
	_rec_name = 'name'
	
	name = fields.Char(copy=False, translate=True)
	ns_ramp_up_id = fields.Many2one('ns.ramp.ups', copy=False)
	ns_sale_id = fields.Many2one('sale.order', string="Sale", copy=False )
	ns_sale_line_id = fields.Many2one('sale.order.line', string="Description", copy=False, domain=[('display_type', '=', False)] )
	ns_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', copy=False, default=0 )
	ns_sale_qty = fields.Float(string='SO Line Qty', digits='Product Unit of Measure', copy=False, default=0 )	
	ns_product_id = fields.Many2one('product.product', copy=False, string="Products" )
	ns_discount = fields.Float(string="Discount", copy=False , default=0 )
	ns_price_unit = fields.Float(string="Unit Price", copy=False , default=0 )
	ns_subtotal = fields.Float(string="Subtotal", copy=False, default=0, store=True)
	ns_annual_fee = fields.Float(copy=False, default=0)
	display_type = fields.Selection([('line_section', "Section"),('line_note', "Note")], default=False, copy=False, translate=True)
	ns_task_id = fields.Many2one('project.task', "TASK" )
	sequence = fields.Integer(string='Sequence', default=10, copy=False)
	ns_remarks = fields.Text("Remarks", translate=True)
	ns_sale_line_unique_id = fields.Char('Unique ID')
	ns_tax_id = fields.Many2many('account.tax', string='Taxes')
	ns_price_total = fields.Float(string="Total", copy=False, default=0, store=True)
	
	

	@api.model
	def create(self, vals):
		ramp_up_lines = super(RampUpsLine, self).create(vals)
		ramp_up_lines.checking_creating_ramp_up_line()
		return ramp_up_lines

	def write(self, vals):
		res = super(RampUpsLine, self).write(vals)
		self.checking_creating_ramp_up_line()
		return res

	def checking_creating_ramp_up_line(self):
		message = False
		if self.ns_sale_line_id and self.ns_qty > self.ns_sale_qty:
			message = 'Quantity tidak boleh lebih besar dari SO Line Qty'
		if message:
			raise exceptions.UserError(message)


	def _timesheet_create_task_prepare_values(self, project):
		self.ensure_one()
		planned_hours = self.ns_sale_line_id._convert_qty_company_hours(self.ns_sale_line_id.company_id)
		sale_line_name_parts = self.name.split('\n')
		title = sale_line_name_parts[0] or self.ns_sale_line_id.product_id.name
		description = '<br/>'.join(sale_line_name_parts[1:])
		result = {
			# 'name': title if project.sale_line_id else '%s: %s' % (self.ns_sale_line_id.order_id.name or '', title),
			'name': '%s' % (self.ns_sale_line_id.order_id.name or ''),
			'planned_hours': planned_hours,
			'partner_id': self.ns_sale_line_id.order_id.partner_id.id,
			'email_from': self.ns_sale_line_id.order_id.partner_id.email,
			'description': description,
			'project_id': project.id,
			'sale_line_id': self.ns_sale_line_id.id,
			'sale_order_id': self.ns_sale_line_id.order_id.id,
			'company_id': project.company_id.id,
			'x_studio_service_request_date': self.ns_ramp_up_id.ns_start_date,
			'user_id': False,  # force non assigned task, as created as sudo()
		}

		if self.ns_sale_line_id.product_template_id.ns_capacity_assignation == 'space_id':
			reserved_spaces = self.env['ns.ns_space'].search([('ns_reserved','=',True), ('ns_sale_order_line_id','=', self.ns_sale_line_id.id)])
			if reserved_spaces:
				result['x_studio_space_id'] = reserved_spaces[0].id

		elif self.ns_sale_line_id.product_template_id.ns_capacity_assignation == 'breaker_id':
			reserved_breaker = self.env['ns.ns_breaker'].search([('ns_reserved','=',True), ('ns_sale_order_line_id','=', self.ns_sale_line_id.id)])
			if reserved_breaker:
				result['x_studio_breaker_id'] = reserved_breaker[0].id

		return result

	def _timesheet_create_task(self, project):
		""" Generate task for the given so line, and link it.
			:param project: record of project.project in which the task should be created
			:return task: record of the created task
		"""
		values = self._timesheet_create_task_prepare_values(project)
		task_qty = self.ns_qty
		values['ns_qty'] = task_qty
		task = self.env['project.task'].sudo().create(values)	
		
		self.write({'ns_task_id': task.id})
		# post message on task
		task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s-%s)") % (self.ns_sale_line_id.order_id.id, self.ns_sale_line_id.order_id.name, self.ns_ramp_up_id.name, self.ns_sale_line_id.product_id.name)
		task.message_post(body=task_msg)
		if not self.ns_sale_line_id.ns_no_sub_task:
			task_to_create = 1 if self.ns_sale_line_id.ns_merge_ib_task else int(self.ns_qty)			
			for i in range(task_to_create):
				values = self._timesheet_create_task_prepare_values(project)
				values['parent_id'] = task.id
				values['sale_order_id'] = False
				values['ns_qty'] = task_qty
				if project.allow_subtasks and project.subtask_project_id:
					values['project_id'] = project.subtask_project_id.id
				child_task = self.env['project.task'].sudo().create(values)
				# child_task['name'] = "%s" % (child_task.name)
				task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s-%s)") % (self.ns_sale_line_id.order_id.id, self.ns_sale_line_id.order_id.name, self.ns_ramp_up_id.name, self.ns_sale_line_id.product_id.name)
				child_task.message_post(body=task_msg)
		return task
