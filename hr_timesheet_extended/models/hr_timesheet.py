# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
from datetime import datetime, date, timedelta

class AccountAnalyticLine(models.Model):
	_inherit = 'account.analytic.line'

	@api.multi
	@api.constrains('unit_amount')
	def _unit_amount_check(self):
		for rec in self:
			if rec.unit_amount > 24:
				raise ValidationError(_("Hours should be less than 24 hours"))

	@api.multi
	def unlink(self):
		if self.filtered(lambda x:x.state not in 'draft'):
			raise UserError(_('You cannot delete the record which is not in draft !..'))
		return super(AccountAnalyticLine, self).unlink()

	@api.model
	@api.onchange('is_approver')
	def _compute_approver(self):
		user_group = self.env['res.users'].has_group('hr.group_hr_manager')
		for each in self:
			if user_group and each.state == 'pending' or each.state =='rejected' :
				each.is_approver = True
			else:
				each.is_approver = False

	@api.multi
	@api.constrains('employee_id', 'date')
	def check_timesheet_existence(self):
		if self.date:
			for timesheet in self.env['account.analytic.line'].search([('date', '=', self.date),('employee_id', '=', self.employee_id.id),('state', 'in', ['approved','pending'])]):
				if timesheet.employee_id == self.employee_id:
					raise ValidationError(_('Already Created a Timesheet for given Date'))

	# Employee check leave master and holiday master and weekoff
	@api.depends('employee_id', 'date')
	def compute_emp_count_days(self):
		for timesheet in self:
			app_date = timesheet.date
			current_date = date.today()
			leave_days = total = day_count = global_days_count = days_leave = leave_count = 0
			week_off_days_count = leave_delta_day = days_block = hol =  var = holiday_count = app_var = 0
			for leave in self.env['hr.leave'].sudo().search([('employee_id','=',timesheet.employee_id.id),('state','=','validate')]):
				# if app_date <= current_date:
				if leave.request_date_from >= app_date and current_date >= leave.request_date_from:
					days_leave =  (leave.request_date_to - leave.request_date_from).days + 1
					leave_count += days_leave
					# Calculate Sunday Between Leave Request
					start_dt = leave.request_date_from
					end_dt = leave.request_date_to
					delta_day = timedelta(days=1)
					days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
					dt = start_dt
					while dt <= end_dt:
						if dt.weekday() == days['Sunday']:
							day_count+=1
						dt += delta_day
			leave_days = (leave_count - day_count)
			holiday_count = (current_date - app_date).days
			for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',timesheet.company_id.id),('work_location_id','=',timesheet.employee_id.lone_manager_id.location_work_id.id)]):
				app_var = holiday.date_from.date()
				if app_var >= app_date and app_var <= current_date:
					var = len(holiday)
					hol += var
			days_block = hol + 3 + leave_days
			start_weekoff = app_date
			end_weekoff = start_weekoff + relativedelta(days=(days_block))
			weekoff_delta_day = timedelta(days=1)
			week_off_days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
			st_dt = start_weekoff
			while st_dt <= end_weekoff:
				if st_dt.weekday() == week_off_days['Sunday']:
					week_off_days_count+=1
				st_dt += weekoff_delta_day
			block_count = week_off_days_count + days_block
			timesheet.emp_count_days = block_count

	@api.onchange('date')
	def timesheet_date(self):
		for rec in self:
			if rec.date:
				current_date = fields.date.today()
				var = current_date
				if rec.date > current_date:
					raise ValidationError(_("Should Enter the timesheet till today actual."))

	name = fields.Char('Description', required=False, size=100)
	state = fields.Selection([('draft','Draft'),('pending','Pending for Approval'),('approved','Approved'),('rejected','Rejected')],string="Status",default="draft")
	description = fields.Char("Description")
	# remarks = fields.Char("Remarks", size=100)
	approver_remarks = fields.Char("Approver Remarks")
	is_approver = fields.Boolean('Is Approver',compute='_compute_approver')
	is_expired = fields.Boolean('Is Expired')
	department1_id = fields.Many2one('hr.department', string="Department",compute='_compute_department1_id')
	submit_date = fields.Date("Submitted Date")
	emp_count_days = fields.Float("Approver Count", compute="compute_emp_count_days")

	@api.onchange('department1_id')
	def onchange_department1_id(self):
		current_user = self.env.uid
		employee = self.env['hr.employee']
		# force domain on task when project is set
		# if self.employee_id:
		# if self.department_id:
		if self.department1_id != self.task_id.department_id:
				# reset task when changing project
			self.task_id = False
		return {'domain': {
				'task_id': [('department_id', '=', self.department1_id.id)]
		}}

	@api.multi
	@api.depends('date')
	def _compute_department1_id(self):
		current_user = self.env.uid
		emp = self.env['hr.employee'].search([('user_id','=',current_user)])
		if emp:
			for line in emp:
				for lines in self:
					lines.department1_id = line.department_id
			
	# Need to add library import datetime
	# Cron to change move time sheets to seperate screen
	@api.multi
	def _cron_expired_timesheet(self):
		current_date = datetime.datetime.now().date()
		seven_days = current_date - datetime.timedelta(days=6)
		print("Seven Days", seven_days)
		timesheet = self.env['account.analytic.line'].search([('date','<',seven_days),('is_expired','=',False)])
		if timesheet:
			for rec in timesheet:
				rec.is_expired = True
	
	@api.multi
	def approve_timesheet(self):
		# flag = self.env['res.users'].has_group('hr_employee_kra.group_kra_approver_1')
		current_user = self.env.uid
		for data in self:
			var = data.employee_id.lone_manager_id.user_id.id
			if var == current_user:
				for line in self.env['account.analytic.line'].browse(self._context.get('active_ids', [])):
					if line:
						for vals in self.env['account.analytic.line'].search([('employee_id','=',line.employee_id.id),('date','=',line.date),('state','=','pending')]):
							vals.state = 'approved'
							vals.write({'approver_remarks' : 'Approved'})
			else:
				raise UserError(_('You are not a authorized user to Approve Timesheets.'))
		
	@api.multi
	def reject_timesheet(self):
		current_user = self.env.uid
		# var = self.employee_id.lone_manager_id.user_id.id
		# if var == current_user:
		for line in self:
			if line.employee_id.lone_manager_id.user_id.id == current_user:
				timesheet = self.env['account.analytic.line'].search([('employee_id','=',line.employee_id.id),('date','=',line.date)])
				if timesheet:
					count = 0
					for lines in timesheet:
						if lines.state == 'pending':
							# lines.write({'state':'pending'})
							form_view = self.env.ref('hr_timesheet_extended.form_approver_reject_wizard')
							return {
								'name': "Approver Remarks",
								'view_mode': 'form',
								'view_type': 'form',
								'view_id': form_view.id,
								'res_model': 'approver.reject.wizard',
								'type': 'ir.actions.act_window',
								'target': 'new',
								'context': {
									'timesheet_id': lines.ids, 'is_reject': True,'employee_id':lines.employee_id.id,'date':lines.date
								}
							}
			else:
				raise UserError(_('You are not a authorized user to Reject Timesheets.'))

	@api.multi
	def submit_timesheet(self):
		# for line in self:
		current_user = self.env.uid
		current_date = fields.date.today()
		var_1 = self.env['account.analytic.line'].search([('user_id', '=', current_user),('state', '=', 'draft')])
		nov = 0
		for rec in var_1:
			if rec.date == rec.date:
				nov += rec.unit_amount
		if nov <= 24:
			for line in self.env['account.analytic.line'].browse(self._context.get('active_ids', [])):
				if line:
					timesheet = self.env['account.analytic.line'].search([('employee_id','=',line.employee_id.id),('date','=',line.date)])
					if timesheet:
						for lines in timesheet:
							if lines.state == 'draft':
								if lines.date + relativedelta(days=(lines.emp_count_days)) <= current_date:
									raise ValidationError(_("Should Allow timesheet Entry for 2 days."))
								else:
									lines.state = 'pending'
									lines.submit_date = current_date

		else:
			raise ValidationError(_('Hours should be less than 24 hours'))

	@api.model
	def _cron_approver_timesheet_validity(self):
		for act_emp in self.env['hr.employee'].sudo().search([('active', '=', True)]):
			if act_emp.lone_manager_id.user_id.is_blocked == False:
				current_date = date.today()
				for timesheet in self.env['account.analytic.line'].sudo().search([('employee_id', '=', act_emp.id),('state', '=', 'pending'),('is_expired', '=', False)], order='id desc'):
					leave_days = total = day_count = global_days_count = days_leave = leave_count = 0
					week_off_days_count = leave_delta_day = days_block = hol =  var = holiday_count = app_var = 0
					app_date = timesheet.write_date.date()
					is_dir = timesheet.employee_id.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
					if is_dir == False:
						for leave in self.env['hr.leave'].sudo().search([('employee_id','=',timesheet.employee_id.lone_manager_id.id),('state','=','validate')]):
							# if app_date <= current_date:
							if leave.request_date_to >= app_date and current_date >= leave.request_date_to:
								days_leave =  (leave.request_date_to - leave.request_date_from).days + 1
								leave_count += days_leave
								# Calculate Sunday Between Leave Request
								start_dt = leave.request_date_from
								end_dt = leave.request_date_to
								delta_day = timedelta(days=1)
								days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
								dt = start_dt
								while dt <= end_dt:
									if dt.weekday() == days['Sunday']:
										day_count+=1
									dt += delta_day
						leave_days = (leave_count - day_count)
						holiday_count = (current_date - app_date).days
						for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',timesheet.company_id.id),('work_location_id','=',timesheet.employee_id.lone_manager_id.location_work_id.id)]):
							app_var = holiday.date_from.date()
							if app_var >= app_date and app_var <= current_date:
								var = len(holiday)
								hol += var
						days_block = hol + 3 + leave_days
						start_weekoff = app_date
						end_weekoff = start_weekoff + relativedelta(days=(days_block))
						weekoff_delta_day = timedelta(days=1)
						week_off_days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
						st_dt = start_weekoff
						while st_dt <= end_weekoff:
							if st_dt.weekday() == week_off_days['Sunday']:
								week_off_days_count+=1
							st_dt += weekoff_delta_day
						block_count = week_off_days_count + days_block
						notify_count = (week_off_days_count + days_block) - 1
						if app_date + relativedelta(days=(block_count)) <= current_date:
							# for vals in timesheet.employee_id:
							timesheet.employee_id.lone_manager_id.user_id.is_blocked = True
							timesheet.employee_id.lone_manager_id.user_id.blocked_date = fields.Date.today()
							timesheet.employee_id.lone_manager_id.block_date = fields.Date.today()
							blocking = self.env['blocked.details'].sudo().search([('date','=',timesheet.date),('employee_id.lone_manager_id','=',timesheet.employee_id.id),('blocked_date','=',current_date)])
							if not blocking:
								block_hist = blocking.create({'blocked_id': timesheet.employee_id.lone_manager_id.id,
												'employee_id' : timesheet.employee_id.id,
												'date': timesheet.date,
												'blocked_date': fields.Date.today(),
												'reason' : 'Timesheet not approved'})
								timesheet.employee_id.lone_manager_id.user_id.login_success = False
								# To create record in 'user account blocking' menu - Starts
								acc = self.env['account.blocking']
								inv_line_obj = acc.sudo().create({'employee_id': timesheet.employee_id.lone_manager_id.id,
													'blocked_date': date.today(),
													'remark':'Timesheet not approved'})
								# template_id = self.env.ref('hr_timesheet_extended.email_template_notification_lone_blocked')
								# template_id.sudo().send_mail(act_emp.id, force_send=True)
							# To create record in 'user account blocking' menu - Ends

						# elif app_date + relativedelta(days=(notify_count)) == current_date:
						# 	for vals in timesheet.employee_id.lone_manager_id:
						# 		template_id = self.env.ref('hr_timesheet_extended.email_template_block_notification_lone_oneday_ago')
						# 		template_id.sudo().send_mail(timesheet.employee_id.id, force_send=True)
	
	# To trigger single mail for multiple employees
	@api.model
	def _cron_single_mail_for_multiple_employees(self):
		curr_date = fields.Date.today()
		for block in self.env['res.users'].sudo().search([('is_blocked','=',True),('blocked_date','=',curr_date)]):
			for employee in self.env['hr.employee'].search([('user_id','=',block.id),('active','=',True),('block_date','=',curr_date)]):
				template_id = self.env.ref('hr_timesheet_extended.email_template_mail_for_multiple_employees')
				template_id.sudo().send_mail(employee.id, force_send=True)

	@api.model
	def _cron_employee_timesheet_validity(self):
		for act_emp in self.env['hr.employee'].sudo().search([('active', '=', True)]):
			if act_emp.user_id.is_blocked == False:
				current_date = date.today()
				timesheet_val = self.env['account.analytic.line'].sudo().search([('employee_id', '=', act_emp.id),('state', 'not in', [('draft'),('rejected')])], order='date desc', limit=1)
				for timesheet in timesheet_val:
					if timesheet:
						leave_days = total = day_count = global_days_count = days_leave = leave_count = emp_var =0
						week_off_days_count = leave_delta_day = days_block = hol =  var = 0
						create_date = timesheet.date
						is_dir = timesheet.employee_id.user_id.has_group('hr_employee_kra.group_kra_director')
						if timesheet.employee_id.timesheet == 'yes':
							if create_date + relativedelta(days=(timesheet.emp_count_days)) <= current_date:
								for vals in timesheet.employee_id:
									vals.user_id.is_blocked = True
									vals.user_id.blocked_date = fields.Date.today()
									vals.block_date = fields.Date.today()
									timesheet.employee_id.user_id.login_success = False
									# To create record in 'Blocked History'- Starts
									blocking = self.env['blocked.details'].sudo().search([('date','=',timesheet.date),('employee_id','=',timesheet.employee_id.id),('blocked_date','=',current_date)])
									if not blocking:
										block_hist = blocking.create({'blocked_id':act_emp.id,
														'employee_id' : timesheet.employee_id.id,
														'date': timesheet.date,
														'blocked_date': fields.Date.today(),
														'reason' : 'No timesheet for last two working days'})
									# To create record in 'Blocked History'- Ends
									# To create record in 'user account blocking' menu - Starts
										acc = self.env['account.blocking']
										inv_line_obj = acc.sudo().create({'employee_id': timesheet.employee_id.id,
															'blocked_date': date.today(),
															'remark':'No timesheet for last two working days'})
				no_timesheet = self.env['account.analytic.line'].sudo().search([('employee_id', '=', act_emp.id),('state', 'not in', [('draft'),('rejected')])])
				if not no_timesheet and act_emp.timesheet == 'yes':
					act_emp.user_id.is_blocked = True
					act_emp.user_id.blocked_date = fields.Date.today()
					act_emp.block_date = fields.Date.today()
					act_emp.user_id.login_success = False
					block_hist = self.env['blocked.details'].sudo().create({'blocked_id':act_emp.id,
						'employee_id' : act_emp.id,
						'date': False,
						'blocked_date': fields.Date.today(),
						'reason' : 'No timesheet for last two working days'})
					acc = self.env['account.blocking']
					inv_line_obj = acc.sudo().create({'employee_id':act_emp.id,
						'blocked_date': date.today(),
						'remark':'No timesheet for last two working days'})

class Project(models.Model):
	_inherit = 'project.project'

	# @api.multi
	# def name_get(self):
	# 	result = []
	# 	for record in self:
	# 		if record.description:
	# 			name = str(record.name) + ' , ' + str(record.description)
	# 		else:
	# 			name = str(record.name)
	# 		result.append((record.id, name))
	# 	return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if not recs:
			recs = self.search(['|',('description',operator,name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()
