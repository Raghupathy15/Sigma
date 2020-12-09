# -*- coding: utf-8 -*-

from datetime import date,datetime
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.addons.resource.models.resource import float_to_time
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError

YEARS = []
for year in range(int(date.today().strftime('%Y')) - 4 , int(date.today().strftime('%Y')) + 1):
   YEARS.append((str(year), str(year)))
class EmployeeConfig(models.Model):
	_inherit = 'hr.employee'

	sandwich = fields.Boolean(string="Apply",default=True)
	leave_notification = fields.Boolean(string="Show Notification")

class GlobalConfig(models.Model):
	_inherit = 'resource.calendar'
	sandwich = fields.Boolean(string="Sandwich Rule",default=True)

	@api.onchange('sandwich')
	def set_sandwich(self):
		for employee in self.env['hr.employee'].search([('resource_calendar_id', '=', self._origin.id)]):
			employee.write({'sandwich': self.sandwich})

class HolidaysRequest(models.Model):
	_inherit = 'hr.leave'

	@api.multi
	def unlink(self):
		if self.filtered(lambda x:x.state not in 'draft'):
			raise UserError(_('You cannot delete the record which is not in draft !..'))
		return super(HolidaysRequest, self).unlink()

	set_notification = fields.Boolean()
	doctor_certificate = fields.Binary('Doctor Certificate (Max~3MB)',required=False)
	filename = fields.Char('Filename')
	holiday_status_name = fields.Char(string='Holiday Status Name', related='holiday_status_id.name')
	work_date = fields.Date('Work Date')
	request_date_from_period = fields.Selection([
		('am', 'Session1'), ('pm', 'Session2')], string="Date Period Start", default="am", required=True)
	request_date_to_period = fields.Selection([
		('am', 'Session1'), ('pm', 'Session2')], string="Date Period To", default="am", required=True)
	resource_calendar_id = fields.Many2one(
		'resource.calendar', 'Company Working Hours',
		related='company_id.resource_calendar_id', readonly=False)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

	leave_year = fields.Selection(YEARS, string="Year", default=date.today().strftime('%Y'))
	state = fields.Selection([
		('draft', 'To Submit'),
		('cancel', 'Cancelled'),
		('confirm', 'Pending'),
		('refuse', 'Rejected'),
		('validate1', 'Second Approval'),
		('validate', 'Approved')
		], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
		help="The status is set to 'To Submit', when a leave request is created." +
		"\nThe status is 'To Approve', when leave request is confirmed by user." +
		"\nThe status is 'Refused', when leave request is refused by manager." +
		"\nThe status is 'Approved', when leave request is approved by manager.")
	report_note = fields.Text('Reason',track_visibility='onchange')
	number_of_days = fields.Float('Duration (Days)', copy=False, readonly=True, track_visibility='onchange',store=True,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
		help='Number of days of the leave request according to your working schedule.', compute='_compute_number_of_days_display')
	number_of_days_display = fields.Float('Duration in days', compute='_compute_number_of_days_display', copy=False, readonly=True,
		help='Number of days of the leave request. Used for interface.',force_save=True)
	duration_count = fields.Float('Duration (Days)', copy=False, readonly=True, compute='_compute_number_of_days_display')

	@api.multi
	@api.depends('employee_id')
	def compute_emp_app1_id(self):
		for vals in self:
			if vals.employee_id.lone_manager_id:
				vals.app_id = vals.employee_id.lone_manager_id.id

	# get Users for Notification/Reminders
	@api.multi
	@api.depends('employee_id')
	def compute_employee_approver1_id(self):
		employee_rec = self.env['hr.employee'].sudo().search([('id', '=', self.employee_id.id)])
		for rec in employee_rec:
			self.hr_reminder_approver1_ids = rec.lone_manager_id
			self.hr_reminder_approver2_ids = rec.ltwo_manager_id
			self.hr_reminder_hod_ids = rec.hod_id
			self.hr_reminder_director_ids = rec.parent_id
			self.employee_ids = rec

	hr_reminder_approver1_ids = fields.Many2many('hr.employee', string='Noti1 Approver1',
												 compute="compute_employee_approver1_id")
	hr_reminder_approver2_ids = fields.Many2many('hr.employee', string='Noti2 Approver2',
												 compute="compute_employee_approver1_id")
	hr_reminder_hod_ids = fields.Many2many('hr.employee', string='Noti3 Hod',
										   compute="compute_employee_approver1_id")
	hr_reminder_director_ids = fields.Many2many('hr.employee', string='Noti4 Director',
												compute="compute_employee_approver1_id")
	employee_ids = fields.Many2many('hr.employee', string='Noti5 Employee Ids', compute="compute_employee_approver1_id")

	app_id = fields.Many2one('hr.employee', string='Approver 1', compute="compute_emp_app1_id")


	# To check request_date_from_period and request_date_to_period
	@api.constrains('date_from', 'date_to','request_date_from_period','request_date_to_period')
	def _check_date(self):
		for holiday in self:
			domain = [
				('date_from', '<', holiday.date_to),
				('request_date_from_period', '=', holiday.request_date_from_period),
				('date_from', '<', holiday.date_to),
				('date_to', '>', holiday.date_from),
				('employee_id', '=', holiday.employee_id.id),
				('id', '!=', holiday.id),
				('state', 'not in', ['cancel', 'refuse']),
			]
			nholidays = self.search_count(domain)
			if nholidays:
				raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

	@api.model
	def default_get(self, fields_list):
		defaults = super(HolidaysRequest, self).default_get(fields_list)
		defaults['holiday_status_id'] = False
		defaults['request_date_from_period'] = False
		return defaults

	@api.multi
	def _create_resource_leave(self):
		""" This method will create entry in resource calendar leave object at the time of holidays validated """
		for leave in self:
			date_from = fields.Datetime.from_string(leave.date_from)
			date_to = fields.Datetime.from_string(leave.date_to)

		#     self.env['resource.calendar.leaves'].create({
		#         'name': leave.name,
		#         'date_from': fields.Datetime.to_string(date_from),
		#         'holiday_id': leave.id,
		#         'date_to': fields.Datetime.to_string(date_to),
		#         'resource_id': leave.employee_id.resource_id.id,
		#         'calendar_id': leave.employee_id.resource_calendar_id.id,
		#         'time_type': leave.holiday_status_id.time_type,
		#     })
		# return True

	@api.constrains('request_date_from', 'request_date_to', 'request_date_from_period', 'request_date_to_period','number_of_days','holiday_status_id')
	def _check_period(self):
		if self.number_of_days > 2 and self.holiday_status_name == 'SL':
			if not self.doctor_certificate:
				raise ValidationError(_('Kindly attach doctor certificate'))
		if self.request_date_from == self.request_date_to:
			if self.request_date_from_period == 'pm':
				if self.request_date_to_period == 'am':
					raise ValidationError(_('For Same Day Session To Anterior'))

	@api.onchange('request_date_from', 'request_date_to')
	def _onchange_req_date_period(self):
		if not self.holiday_status_id.name == 'PL':
			if self.request_date_from_period or self.request_date_to_period:
				self.request_date_from_period = False
				self.request_date_to_period = False

	@api.onchange('request_date_from', 'request_date_to', 'holiday_status_id', 'number_of_days_display')
	def _onchange_check_date_validation(self):
		if self.holiday_status_id and self.request_date_from and self.request_date_to:
			is_admin = self.env.user.has_group('base.group_system')
			# if self.holiday_status_id.name == 'EL':
			# 	if not is_admin:
			# 		if (self.request_date_from - date.today()).days < 2:
			# 			raise ValidationError(_('Apply 1 days in advance'))
			if self.holiday_status_id.name == 'PL':
				if not is_admin:
					if (self.request_date_from - date.today()).days <= 15:
						raise ValidationError(_('Apply 15 days in advance'))
					else:
						import datetime
						new_date = self.request_date_from + datetime.timedelta(days=5)
						self.request_date_to = new_date
						self.number_of_days = 6
						self.request_date_from_period = 'am'
						self.request_date_to_period = 'pm'
			if self.holiday_status_id.name == 'COMP' and self.work_date:
				work_date = self.work_date + relativedelta(days=28)
				if self.request_date_from > work_date:
					raise ValidationError(_('COMP leave avail within 4 weeks'))

	# default module code
	@api.onchange('date_from', 'date_to', 'employee_id')
	def _onchange_leave_dates(self):
		if not self.holiday_status_id.name == 'PL':
			if self.date_from and self.date_to:
				self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)
				# self.number_of_days = self.duration_count
			else:
				self.number_of_days = 0
	
	@api.multi
	def action_cancel(self):
		if self.env.uid != self.employee_id.lone_manager_id.user_id.id:
			if self.env.uid != self.employee_id.ltwo_manager_id.user_id.id:
				raise UserError(_('You are not authorized user to cancel !..'))
			else:
				form_view = self.env.ref('leave_custom.form_cancel_leave_wizard')
				return {
					'name': "Cancel Leave",
					'view_mode': 'form',
					'view_type': 'form',
					'view_id': form_view.id,
					'res_model': 'cancel.leave.wizard',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'context': {
						'leave_id': self.id
					}
				}
				template_id = self.env.ref('leave_custom.email_template_leave_cancel')
				template_id.sudo().send_mail(self.id, force_send=True)
		else:
			form_view = self.env.ref('leave_custom.form_cancel_leave_wizard')
			return {
				'name': "Cancel Leave",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'cancel.leave.wizard',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'leave_id': self.id
				}
			}
			template_id = self.env.ref('leave_custom.email_template_leave_cancel')
			template_id.sudo().send_mail(self.id, force_send=True)

	@api.multi
	def action_reject(self):
		current_user = self.env.uid
		var = self.employee_id.lone_manager_id.user_id.id
		if var != current_user:
			raise ValidationError(_("You are not authorized user to reject this leave"))
		elif var == current_user:
			form_view = self.env.ref('leave_custom.form_reject_leave_wizard')
			return {
				'name': "Reject Leave",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'reject.leave.wizard',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'leave_id': self.id
				}
			}
			template_id = self.env.ref('leave_custom.email_template_leave_rejected')
			template_id.sudo().send_mail(self.id, force_send=True)

	# Default module code
	def activity_update(self):
		to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
		for holiday in self:
			if holiday.state == 'draft':
				to_clean |= holiday
				# print("Draftinggggggggggggggggggg", self.duration_count, self.number_of_days)
			elif holiday.state == 'validate':
				to_do |= holiday
			elif holiday.state == 'refuse':
				to_clean |= holiday

	@api.multi
	def action_validate(self):
		if any(holiday.state not in ['confirm', 'validate1'] for holiday in self):
			raise UserError(_('Leave request must be confirmed in order to approve it.'))
		for order in self:
			if order.state and order.state == 'validate1':
				template_id = self.env.ref('leave_custom.email_template_leave_approval')
				template_id.send_mail(self.id, force_send=True)
		return super(HolidaysRequest, self).action_validate()

	@api.multi
	def action_confirm(self):
		current_user = self.env.uid
		var = self.employee_id.user_id.id
		is_admin = self.env.user.has_group('base.group_system')
		today = datetime.now()
		tdy = today.strftime("%Y")
		if tdy < self.request_date_to.strftime("%Y") and self.holiday_status_id.name == 'SL':
			raise ValidationError(_("You are not allowed to request SL leave for future year ! please use SL leave for current year only"))
		if var != current_user and not is_admin:
			raise ValidationError(_("You are not authorized user to Submit this leave"))
		elif var == current_user or is_admin:
			res = super(HolidaysRequest, self).action_confirm()
			template_id = self.env.ref('leave_custom.email_template_leave_request')
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Leave Request','employee_id': self.employee_id.id, 'model_name': 'hr.leave',
				'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],'hr_leave_id': self.id})
		return res

	# @api.multi
	# def action_submit(self):
	# 	for rec in self:
	# 		rec.write({'state': 'confirm'})

	@api.multi
	def action_approve(self):
		# To create record in attendance - starts
		if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
			date_start = self.request_date_from
			date_end = self.request_date_to  - relativedelta(days=1)
			while date_start <= date_end:
				employee = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
				if employee:
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',date_start),('employee_id','=',employee.id)])
					if not attendance:
						atten = self.env['hr.attendance']
						obj = atten.create({'logged_date': date_start,'employee_id': employee.id,
											'is_leave':True,'leave_id':self.id,'leave_days_onch':1})
						date_start = date_start + relativedelta(days=1)
					elif attendance:
						for vals in attendance:
							vals.write({'is_leave':True})
							date_start = date_start + relativedelta(days=1)
			# To create record for half day
			emp = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
			att = self.env['hr.attendance'].sudo().search([('logged_date','=',self.request_date_to),('employee_id','=',emp.id)],limit=1)
			for mng in att:
				mng.write({'morn_leave':True})
			if not att:
				obj = att.create({'logged_date':self.request_date_to,'employee_id':emp.id,
								'leave_id':self.id,'morn_leave':True})

		elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
			date_start = self.request_date_from + relativedelta(days=1)
			date_end = self.request_date_to
			while date_start <= date_end:
				employee = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
				if employee:
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',date_start),('employee_id','=',employee.id)])
					if not attendance:
						atten = self.env['hr.attendance']
						obj = atten.create({'logged_date': date_start,'employee_id': employee.id,
											'is_leave':True,'leave_id':self.id,'leave_days_onch':1})
						date_start = date_start + relativedelta(days=1)
					elif attendance:
						for vals in attendance:
							vals.write({'is_leave':True})
							date_start = date_start + relativedelta(days=1)
			# To create record for half day
			emp = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
			att = self.env['hr.attendance'].sudo().search([('logged_date','=',self.request_date_from),('employee_id','=',emp.id)],limit=1)
			for evn in att:
				evn.write({'evng_leave':True})
			if not att:
				obj = att.create({'logged_date':self.request_date_from,'employee_id':emp.id,
								'leave_id':self.id,'evng_leave':True})

		elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
			date_start = self.request_date_from
			date_end = self.request_date_to
			while date_start <= date_end:
				employee = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
				if employee:
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',date_start),('employee_id','=',employee.id)])
					if not attendance:
						atten = self.env['hr.attendance']
						obj = atten.create({'logged_date':date_start,'employee_id':employee.id,
											'is_leave':True,'leave_id':self.id,'leave_days_onch':1})
						date_start = date_start + relativedelta(days=1)
					elif attendance:
						for vals in attendance:
							vals.write({'is_leave':True})
							date_start = date_start + relativedelta(days=1)

		elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
			date_start = self.request_date_from + relativedelta(days=1)
			date_end = self.request_date_to  - relativedelta(days=1)
			while date_start <= date_end:
				employee = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
				if employee:
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',date_start),('employee_id','=',employee.id)])
					if not attendance:
						atten = self.env['hr.attendance']
						obj = atten.create({'logged_date': date_start,'employee_id': employee.id,
											'is_leave':True,'leave_id':self.id,'leave_days_onch':1})
						date_start = date_start + relativedelta(days=1)
					elif attendance:
						for vals in attendance:
							vals.write({'is_leave':True})
							date_start = date_start + relativedelta(days=1)
			# To create record for half day
			emp = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
			att = self.env['hr.attendance'].sudo().search([('logged_date','=',self.request_date_from),('employee_id','=',emp.id)],limit=1)
			for evn in att:
				evn.write({'evng_leave':True})
			if not att:
				obj = att.create({'logged_date':self.request_date_from,'employee_id':emp.id,
								'leave_id':self.id,'evng_leave':True})
			emp = self.env['hr.employee'].sudo().search([('id','=',self.employee_id.id)])
			att = self.env['hr.attendance'].sudo().search([('logged_date','=',self.request_date_to),('employee_id','=',emp.id)],limit=1)
			for mng in att:
				mng.write({'morn_leave':True})
			if not att:
				obj = att.create({'logged_date':self.request_date_to,'employee_id':emp.id,
								'leave_id':self.id,'morn_leave':True})
		# To create record in attendance - ends

		current_employee = self.env.uid
		var = self.employee_id.lone_manager_id.user_id.id
		if var != current_employee:
			raise UserError(_('You are not a authorized user to Approve this Leave.'))
		else:
			# default code starts
			if any(holiday.state != 'confirm' for holiday in self):
				raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
			current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
			self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
			self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
			if not self.env.context.get('leave_fast_create'):
				self.activity_update() 
			# print("Durations", self.duration_count, self.number_of_days)
			# default code ends
			template_id = self.env.ref('leave_custom.email_template_leave_approval')
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Your Leave Has Been Approved',
				'employee_id': self.employee_id.id, 'model_name': 'hr.leave',
				'approver_ids': [(6, 0, self.employee_ids.ids)],
				'hr_leave_id': self.id
			})
		return True

	@api.multi
	def action_refuse(self):
		current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		cur_emp = self.env.uid
		# print("AAA", cur_emp)
		var = self.employee_id.lone_manager_id.user_id.id
		# print("CCC", var)
		if var != cur_emp:
			raise UserError(_('You are not a authorized user to Reject this Leave.'))
		elif var == cur_emp:
			template_id = self.env.ref('leave_custom.email_template_leave_rejected')
			for holiday in self:
				if holiday.state not in ['confirm', 'validate', 'validate1']:
					raise UserError(_('Leave request must be confirmed or validated in order to refuse it.'))

				if holiday.state == 'validate1':
					template_id.sudo().send_mail(self.id, force_send=True)
					holiday.write({'state': 'refuse', 'first_approver_id': current_employee.id})
				else:
					template_id.sudo().send_mail(self.id, force_send=True)
					holiday.write({'state': 'refuse', 'second_approver_id': current_employee.id})
				# Delete the meeting
				if holiday.meeting_id:
					holiday.meeting_id.unlink()
				# If a category that created several holidays, cancel all related
				holiday.linked_request_ids.action_refuse()
			self._remove_resource_leave()
			self.activity_update()
			return True

	# Cron for Allocate EL and SL leave per month
	@api.model
	def _cron_allocate_el_sl_leave_monthly(self):
		cron_hist = self.env['cron.history']
		obj = cron_hist.create(
			{'date': date.today(), 'user_id': self.env.user.id, 'remark': 'Cron for Allocate EL and SL leave per month'})
		for employee in self.env['hr.employee'].sudo().search([('employment_status', '=', 'confirmed'), ('active', '=', True)]):
			if employee:
				el_count = 0
				el_leaves = self.env['hr.leave.type'].sudo().search([('name', '=', 'EL'),('company_id', '=',employee.company_id.id)])
				for el_leave in el_leaves:
					if el_leave:
						for el_id in self.env['hr.leave.allocation'].sudo().search([('employee_id', '=', employee.id),('state', '=', 'validate'),('holiday_status_id', '=', el_leave.id)],limit=1):
							if el_id.el_sl_date:
								start_date = date.today().replace(day=1)
								end_date = date.today().replace(day=1) + relativedelta(months=1) - timedelta(1)
								if el_id.el_sl_date >= start_date and el_id.el_sl_date <= end_date:
									continue
								else:
									el_count = el_id.number_of_days+1
									el_id.number_of_days = el_count
									el_id.el_sl_date = date.today()
							else:
								el_count = el_id.number_of_days+1
								el_id.number_of_days = el_count
								el_id.el_sl_date = date.today()
						
				sl_count = 0
				count_days = 0
				month = date.today().strftime("%B")
				sl_leaves = self.env['hr.leave.type'].sudo().search([('name', '=', 'SL'),('company_id', '=',employee.company_id.id)])
				for sl_leave in sl_leaves:
					if sl_leave:
						for sl_id in self.env['hr.leave.allocation'].sudo().search([('employee_id', '=', employee.id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)],limit=1):
							if sl_id.el_sl_date:
								start_date = date.today().replace(day=1)
								end_date = date.today().replace(day=1) + relativedelta(months=1) - timedelta(1)
								if sl_id.el_sl_date >= start_date and sl_id.el_sl_date <= end_date:
									continue
								elif month == 'January':
									for leave in self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)]):
										count_days += leave.number_of_days
									sl_count = count_days+1
									sl_id.number_of_days = sl_count
									sl_id.el_sl_date = date.today()
								else:
									sl_count = sl_id.number_of_days_display+1
									sl_id.number_of_days = sl_count
									sl_id.el_sl_date = date.today()
							elif month == 'January':
								for leave in self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id),('state', '=', 'validate'),('holiday_status_id', '=', 'SL'),('company_id', '=',employee.company_id.id)]):
									count_days += leave.number_of_days
								sl_count = count_days+1
								sl_id.number_of_days = sl_count
								sl_id.el_sl_date = date.today()
							else:
								sl_count = sl_id.number_of_days_display+1
								sl_id.number_of_days = sl_count
								sl_id.el_sl_date = date.today()

	# Cron for Allocate PL after 1 year complete
	@api.model
	def _cron_allocate_pl_leave_year_complete(self):
		cron_hist = self.env['cron.history']
		obj = cron_hist.create({'date': date.today(),'user_id': self.env.user.id,'remark': 'Cron for Allocate PL after 1 year complete'})
		for employee in self.env['hr.employee'].sudo().search([('active', '=', True)]):
			if employee.joining_date:
				pl_count = 0
				pl_leaves = self.env['hr.leave.type'].sudo().search([('name','=','PL'),('company_id', '=',employee.company_id.id)])
				for pl_leave in pl_leaves:
					if pl_leave:
						for pl_id in self.env['hr.leave.allocation'].sudo().search([('employee_id','=',employee.id),('state','=','validate'),('holiday_status_id','=',pl_leave.id)]):
							current_date = date.today()
							join_date = employee.joining_date
							import datetime
							var_pl = str(join_date.month) + '-' + str(join_date.day) + '-' +  str(current_date.year)
							slist = var_pl.split("-")
							sdate = datetime.date(int(slist[2]),int(slist[0]),int(slist[1]))
							pl_id.pl_date = sdate
							if pl_id.number_of_days_display < 6 and sdate == current_date:
								pl_count = pl_id.number_of_days_display+6
								pl_id.number_of_days = pl_count
								pl_id.pl_date = date.today()

	# Method to calculate Duration

	@api.one
	@api.depends('request_date_from', 'request_date_to', 'request_date_from_period', 'request_date_to_period')
	def _compute_number_of_days_display(self):
		global_count = False
		current_date = fields.date.today()
		# print("Current Date", current_date)
		if self.request_date_from:
			yes_date = self.request_date_from - timedelta(1)
			# print("Previous date", yes_date)
			attendance = self.env['hr.attendance'].sudo().search([('employee_id.user_id', '=', self.env.uid)],order="id desc",limit=1)
			# print("Attendance Entry Exist", attendance)
			rec = self.env['hr.leave'].sudo().search([('user_id', '=', self.env.uid),('state', 'in',('confirm','validate','validate1'))],order="id desc",limit=1)
			# print("Leave Entry Exist", rec)
			leaves = self.env['resource.calendar.leaves'].sudo().search([('work_location_id','=',self.employee_id.location_work_id.id)])
			# print("Resource Calendar Leaves", leaves.name)
			for leave in leaves:
				global_from = datetime.strptime(str(leave.date_from), "%Y-%m-%d %H:%M:%S").date()
				global_to = datetime.strptime(str(leave.date_to), "%Y-%m-%d %H:%M:%S").date()
				if yes_date == global_from or yes_date == global_to:
					global_count = global_from
					# print("Global Leave", global_count)
			week_off = self.env['resource.calendar.weekoffs'].sudo().search([('name', '=', 6)])
			# print("Predefined week off", week_off)

	#If Attendance Recored Exit

			if attendance:
				# checkin_date= datetime.strptime(str(attendance.check_in), "%Y-%m-%d %H:%M:%S").date()
				checkin_date= attendance.logged_date
				# print("Check In Date", checkin_date)
				if yes_date == checkin_date:
					# print("Previous Date same with attendance Check In date")
					if self.request_date_from == self.request_date_to:
						if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
							# print("Session1")
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
							# print("Session 1a")
							dev = ((self.request_date_to - self.request_date_from).days)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
							# print("Session2 same")
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1

					else:
						if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
							# self.number_of_days = str(( self.request_date_to - self.request_date_to).days)
							dev = ((self.request_date_to - self.request_date_from).days)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
							# self.number_of_days = str(( self.request_date_to - self.request_date_to).days)
							dev = ((self.request_date_to - self.request_date_from).days)
							dev_1 = dev
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1

				elif yes_date != checkin_date:

				# If Leave Record Exist

					if rec:
						# print("Leave record Exist")
						if yes_date == rec.request_date_to:
							if self.request_date_from == self.request_date_to:
								if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
									self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
									self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
									self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
								elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
									self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
									self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
									self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
								elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
									dev = self.number_of_days = (( self.request_date_to - self.request_date_to).days - 0.5)
									dev_1 = dev + 1
									self.number_of_days = dev_1
									self.duration_count = dev_1
									self.number_of_days_display = dev_1
							elif self.request_date_from != self.request_date_to:
								if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
									self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
									self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
									self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
								elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
									self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
									self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
									self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
								elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
									dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days - 0.5)
									dev_1 = dev + 1
									self.number_of_days = dev_1
									self.duration_count = dev_1
									self.number_of_days_display = dev_1
								elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
									dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days)
									dev_1 = dev
									self.number_of_days = dev_1
									self.duration_count = dev_1
									self.number_of_days_display = dev_1

						elif yes_date != rec.request_date_to:
							if global_count:
								yes_day_2 = global_count - timedelta(1)
								# print("Global Previous Day", yes_day_2)
								if yes_day_2 == checkin_date:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

								elif yes_day_2 != checkin_date:
									today = yes_day_2.strftime("%A")
									# print("Day in Alpha", today)
									if today == 'Sunday':
										yes_day_3 = yes_day_2 - timedelta(1)
										# print("Previous Day of Sunday", yes_day_3)
										if yes_day_3 == checkin_date:
											if self.request_date_from == self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													# print("Session1")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													# print("Session 1a")
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													# print("Session2 same")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

											else:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

										elif yes_day_3 != checkin_date:
											if yes_day_3 == rec.request_date_to:
												if self.request_date_from == self.request_date_to:
													if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
														self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
														self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
														self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
														self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
														self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
														self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
														self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
														self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
														self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
														dev = self.number_of_days = (( self.request_date_to - self.request_date_to).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
												elif self.request_date_from != self.request_date_to:
													if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
														self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
														self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
														self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
														self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
														self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
														self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
														dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
														dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days)
														dev_1 = dev
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1

											elif yes_day_3 != rec.request_date_to:
												if self.request_date_from == self.request_date_to:
													if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
														# print("Session1")
														dev = ((self.request_date_to - self.request_date_from).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
														# print("Session 1a")
														dev = ((self.request_date_to - self.request_date_from).days)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
														# print("Session2 same")
														dev = ((self.request_date_to - self.request_date_from).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1

												else:
													if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
														dev = ((self.request_date_to - self.request_date_from).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
														dev = ((self.request_date_to - self.request_date_from).days)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
														dev = ((self.request_date_to - self.request_date_from).days)
														dev_1 = dev
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1
													elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
														dev = ((self.request_date_to - self.request_date_from).days - 0.5)
														dev_1 = dev + 1
														self.number_of_days = dev_1
														self.duration_count = dev_1
														self.number_of_days_display = dev_1

									elif today != 'Sunday':
										if yes_day_2 == rec.request_date_to:
											if self.request_date_from == self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_to).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
											elif self.request_date_from != self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days)
													dev_1 = dev
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

										elif yes_day_2 != rec.request_date_to:
											if self.request_date_from == self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													# print("Session1")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													# print("Session 1a")
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													# print("Session2 same")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

											else:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

							elif not global_count:
								today = yes_date.strftime("%A")
								if today == 'Sunday':
									yes_day_4 = yes_date - timedelta(1)
									# print("Previous Day of Sunday", yes_day_4)
									if yes_day_4 == checkin_date:
										if self.request_date_from == self.request_date_to:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												# print("Session1")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												# print("Session 1a")
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
												# print("Session2 same")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

										else:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

									elif yes_day_4 != checkin_date:
										if yes_day_4 == rec.request_date_to:
											if self.request_date_from == self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_to).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
											elif self.request_date_from != self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
													self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
													self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days)
													dev_1 = dev
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

										elif yes_day_4 != rec.request_date_to:
											if self.request_date_from == self.request_date_to:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													# print("Session1")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													# print("Session 1a")
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
													# print("Session2 same")
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

											else:
												if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
													dev = ((self.request_date_to - self.request_date_from).days)
													dev_1 = dev
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1
												elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
													dev = ((self.request_date_to - self.request_date_from).days - 0.5)
													dev_1 = dev + 1
													self.number_of_days = dev_1
													self.duration_count = dev_1
													self.number_of_days_display = dev_1

							# previous day not in sunday
								if today != 'Sunday':
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1


				#If Leave Record Does not exit

					elif not rec:

					# If Global Leave Exist

						if global_count:
							yes_day_2 = global_count - timedelta(1)
							# print("Global Previous Day", yes_day_2)
							if yes_day_2 == checkin_date:
								if self.request_date_from == self.request_date_to:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										# print("Session1")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										# print("Session 1a")
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
										# print("Session2 same")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1

								else:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1

							elif yes_day_2 != checkin_date:
								today = yes_day_2.strftime("%A")
								# print("Day in Alpha", today)
								if today == 'Sunday':
									yes_day_3 = yes_day_2 - timedelta(1)
									# print("Previous Day of Sunday", yes_day_3)
									if yes_day_3 == checkin_date:
										if self.request_date_from == self.request_date_to:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												# print("Session1")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												# print("Session 1a")
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
												# print("Session2 same")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

										else:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

									elif yes_day_3 != checkin_date:
										if self.request_date_from == self.request_date_to:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												# print("Session1")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												# print("Session 1a")
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
												# print("Session2 same")
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

										else:
											if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
												dev = ((self.request_date_to - self.request_date_from).days)
												dev_1 = dev
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1
											elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
												dev = ((self.request_date_to - self.request_date_from).days - 0.5)
												dev_1 = dev + 1
												self.number_of_days = dev_1
												self.duration_count = dev_1
												self.number_of_days_display = dev_1

								if today != 'Sunday':
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

					# Previous day not in global
						elif not global_count:
							today = yes_date.strftime("%A")
							if today == 'Sunday':
								yes_day_4 = yes_date - timedelta(1)
								# print("Previous Day of Sunday", yes_day_4)
								if yes_day_4 == checkin_date:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

								elif yes_day_4 != checkin_date:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

						# previous day not in sunday
							if today != 'Sunday':
								if self.request_date_from == self.request_date_to:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										# print("Session1")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										# print("Session 1a")
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
										# print("Session2 same")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1

								else:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1


	# If Attendance Record Does not Exits
			elif not attendance:
				# print("Not Attendance Record")

			# If Leave Record Exist

				if rec:
					# print("Not In Loop5")
					if yes_date == rec.request_date_to:
						if self.request_date_from == self.request_date_to:
							if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
								self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
								self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
								self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
							elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
								self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
								self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
								self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
							elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
								self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
								self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
								self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
							elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
								dev = (( self.request_date_to - self.request_date_to).days - 0.5)
								dev_1 = dev + 1
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1
						elif self.request_date_from != self.request_date_to:
							if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
								self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
								self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
							elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
								self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
								self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
							elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
								dev = (( self.request_date_to - self.request_date_from).days - 0.5)
								dev_1 = dev + 1
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1
							elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
								dev = (( self.request_date_to - self.request_date_from).days)
								dev_1 = dev
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1
					elif yes_date != rec.request_date_to:
						if global_count:
							yes_day_2 = global_count - timedelta(1)
							# print("Global Previous Day", yes_day_2)
							today = yes_day_2.strftime("%A")
							# print("Day in Alpha", today)
							if today == 'Sunday':
								yes_day_3 = yes_day_2 - timedelta(1)
								# print("Previous Day of Sunday", yes_day_3)
								if yes_day_3 == rec.request_date_to:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_to).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
									elif self.request_date_from != self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = self.number_of_days = (( self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

								elif yes_day_3 != rec.request_date_to:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

							elif today != 'Sunday':
								if yes_day_2 == rec.request_date_to: 
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_to).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
									elif self.request_date_from != self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = (( self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

								elif yes_day_2 != rec.request_date_to:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
						elif not global_count:
							today = yes_date.strftime("%A") 
							if today == 'Sunday':
								yes_day_4 = yes_date - timedelta(1)
								# print("Previous Day of Sunday", yes_day_4)
								if yes_day_4 == rec.request_date_to:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_to).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
									elif self.request_date_from != self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days - 0.5)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days - 0.5)
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											self.number_of_days = str(( self.request_date_to - rec.request_date_to).days)
											self.duration_count = str(( self.request_date_to - rec.request_date_to).days)
											self.number_of_days_display = str(( self.request_date_to - rec.request_date_to).days)
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											dev = (( self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = (( self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
								elif yes_day_4 != rec.request_date_to:
									if self.request_date_from == self.request_date_to:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											# print("Session1")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											# print("Session 1a")
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
											# print("Session2 same")
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1

									else:
										if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
											dev = ((self.request_date_to - self.request_date_from).days)
											dev_1 = dev
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
										elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
											dev = ((self.request_date_to - self.request_date_from).days - 0.5)
											dev_1 = dev + 1
											self.number_of_days = dev_1
											self.duration_count = dev_1
											self.number_of_days_display = dev_1
						# previous day not in sunday
							if today != 'Sunday':
								if self.request_date_from == self.request_date_to:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										# print("Session1")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										# print("Session 1a")
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
										# print("Session2 same")
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1

								else:
									if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
										dev = ((self.request_date_to - self.request_date_from).days)
										dev_1 = dev
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1
									elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
										dev = ((self.request_date_to - self.request_date_from).days - 0.5)
										dev_1 = dev + 1
										self.number_of_days = dev_1
										self.duration_count = dev_1
										self.number_of_days_display = dev_1

			# If Leave Record Does not exist

				elif not rec:
					# print("Not Leave Record")
					if self.request_date_from == self.request_date_to:
							if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
								# print("Session1")
								dev = ((self.request_date_to - self.request_date_from).days - 0.5)
								dev_1 = dev + 1
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1
							elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
								# print("Session 1a")
								dev = ((self.request_date_to - self.request_date_from).days)
								dev_1 = dev + 1
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1
							elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
								# print("Session2 same")
								dev = ((self.request_date_to - self.request_date_from).days - 0.5)
								dev_1 = dev + 1
								self.number_of_days = dev_1
								self.duration_count = dev_1
								self.number_of_days_display = dev_1

					else:
						if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
							dev = ((self.request_date_to - self.request_date_from).days)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
							dev = ((self.request_date_to - self.request_date_from).days)
							dev_1 = dev
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm': 
							dev = ((self.request_date_to - self.request_date_from).days - 0.5)
							dev_1 = dev + 1
							self.number_of_days = dev_1
							self.duration_count = dev_1
							self.number_of_days_display = dev_1