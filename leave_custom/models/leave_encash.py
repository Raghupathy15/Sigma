# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

YEARS = []
for year in range(int(date.today().strftime('%Y')) - 4 , int(date.today().strftime('%Y')) + 1):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
		  ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
		  ('11', 'November'), ('12', 'December')]

class LeaveEncash(models.Model):
	_name = 'leave.encash'
	_description = 'Leave Encashment'
	_inherit = ['mail.thread']
	_rec_name = 'employee_id'

	def _default_employee_get(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	def _default_leave_type(self):
		return self.env['hr.leave.type'].search([('name', '=', 'EL')], limit=1)

	def _default_approver_one(self):
		emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		approver_id = 0
		for line in emp:
			approver_id = line.lone_manager_id.id
		return approver_id

	def _default_department(self):
		emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		department_id = 0
		for line in emp:
			department_id = line.department_id.id
		return department_id

	name = fields.Char(string="Sequence No.")
	employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get,readonly=True)
	lone_manager_id = fields.Many2one('hr.employee',string="Approver 1",default=_default_approver_one,readonly=True)
	department_id = fields.Many2one('hr.department',string="Department",default=_default_department,readonly=True)
	holiday_status_id = fields.Many2one('hr.leave.type', string='Leave Type', default=_default_leave_type)
	previous_year = fields.Char('Previous Year')
	total_leave = fields.Char('Total Leave of Selected Year', compute="fetch_total_leave_allocated")
	remaining_leave = fields.Float('Remaining Leave of Selected Year',compute="compute_remaining_leaves",store=True)
	# state = fields.Selection([('draft', 'Draft'), ('sent_approval', 'Submit for Approval'), ('approved', 'Approved'),('paid', 'Paid')],
	state = fields.Selection([('draft', 'Draft'),('submit', 'Submited')],string='Status', default='draft')
	requested_date = fields.Date(string='Requested Date',default=datetime.today().strftime('%Y-%m-%d'))
	notes = fields.Text('Remarks')
	is_approver_1 = fields.Boolean(string="Is Approver",compute="_check_approver_one")
	#customizing
	from_year = fields.Selection(YEARS, string="Year of Encashment", default=date.today().strftime('%Y'))
	year = fields.Char(string="Year of Encashment")

	current_year = fields.Selection(YEARS, string="Current Year", default=date.today().strftime('%Y'))
	payslip_id = fields.Many2one("hr.payslip", string="Payslip")
	processing_month = fields.Selection(PERIOD, string="Current Month", default=date.today().strftime('%m'))

	required_days = fields.Float('Required Encashment days')
	previous_remaining_leave = fields.Float('Leave of Pre-Year',compute="compute_pre_remaining_leave",store=True)
	is_user = fields.Boolean('Is User',compute="compute_remaining_leaves")

	@api.multi
	@api.depends('employee_id','from_year')
	def compute_pre_remaining_leave(self):
		for rec in self:
			if rec.remaining_leave < 3:
				rec.previous_remaining_leave = 0
			elif rec.processing_month == '01':
				rec.previous_remaining_leave = rec.remaining_leave - 1
			elif rec.processing_month == '02':
				rec.previous_remaining_leave = rec.remaining_leave - 2

	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('leave.encash')
		rec = super(LeaveEncash,self).create(vals)
		return rec

	@api.multi
	def unlink(self):
		if self.filtered(lambda x:x.state not in 'draft'):
			raise UserError(_('You cannot delete the record which is not in draft !..'))
		return super(LeaveEncash, self).unlink()

	@api.multi
	@api.depends('employee_id','from_year')
	def fetch_total_leave_allocated(self):
		year_value = 0
		for line in self:
			year_value = line.from_year
			employee_id = self.env['hr.employee'].search([('id','=',line.employee_id.id)])
			if employee_id:
				for employee in employee_id:
					allocated_days = 0
					removed_days = 0
					total_leave_pending = 0
					leave_status_add = self.env['hr.leave.allocation'].sudo().search([('employee_id.id', '=', employee.id),
																						  ('holiday_status_id', '=', line.holiday_status_id.id),
																						  ('state', '=', 'validate'),('allocation_year','=',year_value)
																						 ])
					for add in leave_status_add:
						allocated_days += add.number_of_days
					line.total_leave = allocated_days


	@api.multi
	@api.depends('employee_id','from_year')
	def compute_remaining_leaves(self):
		year_value = 0
		for line in self:
			if line.employee_id.user_id.id == line.env.uid:
				line.is_user = True
				print ('111111111111111111',line.employee_id.user_id.id,line.env.uid,line.is_user)
			if not line.processing_month == '01':
				if not line.processing_month == '02':
					raise ValidationError(_("You are allowed to raise 'Encashment request' only in January or February"))
			if line.employee_id:
				res = line.requested_date + relativedelta(years=-1)
				year = line.requested_date.year
				line.year = year - 1

			line.user_id = self.env.user
			total_el = 0
			if line.user_id:
				val = self.env['hr.leave.allocation'].search([('employee_id.user_id.name','=', line.user_id.name),
																('holiday_status_id','=',line.holiday_status_id.id),
																('state','=', 'validate')])
				for data in val:
					total_el += data.number_of_days_display
					line.remaining_leave = total_el

			employee_id = self.env['hr.employee'].search([('id','=',line.employee_id.id)])
			if employee_id:
				for employee in employee_id:
					allocated_days = 0
					removed_days = 0
					total_leave_pending = 0
					leave_status_add = self.env['hr.leave.allocation'].sudo().search([('employee_id.id', '=', employee.id),
																						  ('holiday_status_id', '=', line.holiday_status_id.id),
																						  ('state', '=', 'validate')])
					leave_status_remove = self.env['hr.leave'].sudo().search([('employee_id.id', '=', employee.id),
																				  ('holiday_status_id', '=', line.holiday_status_id.id),
																				  ('state', '=', 'validate')])
					pending_leaves = self.env['hr.leave'].sudo().search([('employee_id.id', '=', employee.id),
																				  ('holiday_status_id', '=', line.holiday_status_id.id),
																				  ('state', '!=', ('validate','cancel','refuse'))])
					if pending_leaves:
						raise ValidationError(_("You are allowed to apply for 'Encashment' after approving of all EL leaves"))
					for add in leave_status_add:
						allocated_days += add.number_of_days
					for remove in leave_status_remove:
						removed_days += remove.number_of_days
					total_leave_pending = allocated_days - removed_days
					line.remaining_leave = total_leave_pending

	@api.model
	@api.depends('remaining_leave')
	def _check_approver_one(self):
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if is_approver_1:
				line.is_approver_1 = True
			else:
				line.is_approver_1 = False

	@api.multi
	def send_for_approval_encash(self):
		if self.required_days < 1:
			raise ValidationError(_("'Required Encashment days' should be greater than 0."))
		if self.required_days > self.previous_remaining_leave:
			raise ValidationError(_("'Required Encashment days' should be less than 'Leave of Pre-Year'."))
		record = self.env['leave.encash'].search([('employee_id.id','=', self.employee_id.id),
																	('year','=',self.year),
																	('state','=','submit')])
		for data in record:
			if data:
				raise ValidationError(_("You have already raised 'Leave Encashment' for the same year. Kindly refer %s" %(data.name)))
		
		if not self.processing_month == '01':
			if not self.processing_month == '02':
				raise ValidationError(_("You are allowed to raise 'Encashment request' only in January or February"))
		# self.state = 'sent_approval'
		self.state = 'submit'
		ctx = dict(self.env.context or {})
		group_id = [self.env.ref('hr.group_hr_manager').id]
		group = self.env['res.groups'].search([('id', 'in', group_id)])
		if group:
			user_ids = self.env['res.users'].sudo().search([('groups_id', 'in', [group.id])])
			email_to = ''.join(['user.partner_id.email' + ',' for user in user_ids])
			email_to = email_to[:-1]
		template_id = self.env.ref('leave_custom.email_template_leave_encashment_request', False)
		ctx.update({
			'email_to': email_to,
		})
		template_id.with_context(ctx).sudo().send_mail(self.id, force_send=True)

		# To update the previous year EL Starts
		state = 0
		for line in self:
			line.user_id = self.env.user
			if line.user_id:
				val = self.env['hr.leave.allocation'].search([('employee_id.user_id.name','=', line.user_id.name),
																('holiday_status_id','=',line.holiday_status_id.id),
																('state','=', 'validate')])
				tot_leaves = (val.number_of_days_display - line.required_days)
				val.number_of_days_display = tot_leaves
				val.sudo().write({'number_of_days':tot_leaves})
		# To update the previous year EL Ends

class HrLeaveAllocation(models.Model):
	_inherit = 'hr.leave.allocation'
	allocation_year = fields.Char(string="Allocated Year",compute="check_year",store=True)
	is_create = fields.Boolean(string="Create",default=False)
	
	@api.multi
	@api.depends('create_date','employee_id')
	def check_year(self):
		for line in self:
			if line.create_date:
				line.allocation_year = fields.Datetime.from_string(line.create_date).year

	# Cron for SL Refuse
	# @api.model
	# def _cron_sl(self):
	# 	for vals in self.env['hr.leave.allocation'].search([('holiday_status_id.name','=','SL'),('state','=','validate'),('is_create','=',False)]):
	# 		today = datetime.now()
	# 		tdy = today.strftime("%Y")
	# 		if vals.allocation_year < tdy:
	# 			vals.state = 'refuse'
	# 			vals.notes = 'Auto refused due to previous year SL'
	# 	return True

	# Cron for SL Create
	@api.model
	def _cron_sl_create(self):
		today = datetime.now()
		tdy = today.strftime("%Y")
		for emp in self.env['hr.employee'].sudo().search([('active','=',True)]):
			allocation = self.env['hr.leave.allocation'].search([('employee_id','=',emp.id),('holiday_status_id.name','=','EL'),('state','=','validate'),('allocation_year','=',str(datetime.now().year))])
			if not allocation:
				count_days = 0
				for leave in self.env['hr.leave'].sudo().search([('employee_id','=',emp.id),('state','not in',['refuse','cancel']),('holiday_status_id.name','=','SL'),('leave_year','=',int(tdy)-1)]):
					count_days += leave.number_of_days
				sl_leaves = self.env['hr.leave.type'].sudo().search([('name', '=', 'EL'),('company_id', '=',emp.company_id.id)])
				for sl_leave in sl_leaves:
					if sl_leave:
						create_alloc = self.env['hr.leave.allocation'].sudo().create({
							'employee_id' : emp.id,
							'holiday_status_id' : sl_leave.id,
							'number_of_days' : count_days,
							'duration_display' : count_days,
							'name': 'EL Leave ' + str(datetime.now().month) + str(datetime.now().year),
							'state' : 'validate',
							'allocation_year' : str(datetime.now().year),
							# 'is_create':True,
							})

	# Cron for PL(6)
	# @api.model
	# def _cron_pl(self):
	# 	for vals in self.env['hr.leave.allocation'].search([('holiday_status_id.name','=','PL'),('state','=','validate')]):
	# 		one_year_after  = vals.employee_id.joining_date + relativedelta(months=12)
	# 		if datetime.today().date() == one_year_after:
	# 			vals.state = 'refuse'
	# 			vals.notes = 'Auto refused due to previous year PL'
	# 		crt_date = vals.create_date.date() + relativedelta(months=12)
	# 		if crt_date <= fields.Date.today():
	# 			vals.state = 'refuse'
	# 			vals.notes = 'Auto refused due to previous year PL'
	# 	return True