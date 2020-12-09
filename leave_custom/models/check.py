# -*- coding: utf-8 -*-

from datetime import date,datetime
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError, UserError

from datetime import timedelta

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
	set_notification = fields.Boolean()

	doctor_certificate = fields.Binary('Doctor Certificate',required=False)
	filename = fields.Char('Filename')
	holiday_status_name = fields.Char(string='Holiday Status Name', related='holiday_status_id.name')
	work_date = fields.Date('Work Date')
	request_date_to_period = fields.Selection([
		('am', 'Session1'), ('pm', 'Session2')], string="Date Period To")
	request_date_from_period = fields.Selection([
		('am', 'Session1'), ('pm', 'Session2')],
		string="Date Period Start", default='am')
	resource_calendar_id = fields.Many2one(
		'resource.calendar', 'Company Working Hours',
		related='company_id.resource_calendar_id', readonly=False)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

	leave_year = fields.Selection(YEARS, string="Year", default=date.today().strftime('%Y'))

	@api.model
	def default_get(self, fields_list):
		defaults = super(HolidaysRequest, self).default_get(fields_list)
		defaults['holiday_status_id'] = False
		defaults['request_date_from_period'] = False
		return defaults

	@api.onchange('request_date_from', 'request_date_to', 'holiday_status_id', 'number_of_days_display')
	def _onchange_check_date_validation(self):
		if self.holiday_status_id and self.request_date_from and self.request_date_to:
			if self.holiday_status_id.name == 'EL':
				if (self.request_date_from - date.today()).days < 2:
					raise ValidationError(_('Apply 1 days in advance'))
			elif self.holiday_status_id.name == 'PL':
				if (self.request_date_from - date.today()).days <= 30:
					raise ValidationError(_('Apply 1 month in advance'))
				if self.number_of_days_display < 6:
					raise ValidationError(_('Can be applied 6 days continues'))
			if self.holiday_status_id.name == 'COMP' and self.work_date:
				work_date = self.work_date + relativedelta(days=28)
				if self.request_date_from > work_date:
					raise ValidationError(_('COMP leave avail within 4 weeks'))

	# @api.multi
	# @api.depends('number_of_days','request_date_from_period','request_date_to_period')
	# def _compute_number_of_days_display(self):
	# 	for holiday in self:
	# 		if holiday.request_date_from_period == 'am' and holiday.request_date_to_period == 'am':
	# 			holiday.number_of_days_display = holiday.number_of_days - 0.5
	# 		elif holiday.request_date_from_period == 'am' and holiday.request_date_to_period == 'pm':
	# 			holiday.number_of_days_display = holiday.number_of_days
	# 		elif holiday.request_date_from_period == 'pm' and holiday.request_date_to_period == 'am':
	# 			holiday.number_of_days_display = holiday.number_of_days - 1
	# 		elif holiday.request_date_from_period == 'pm' and holiday.request_date_to_period == 'pm':
	# 			holiday.number_of_days_display = holiday.number_of_days - 0.5
	# 		else:
	# 			holiday.number_of_days_display = holiday.number_of_days
	# @api.multi
	# def check_lop(self):
	# 	last_leave_date = delta =0
	# 	if self.date_from and self.date_to:
	# 		# weekoff_id = self.env['resource.calendar.weekoffs'].search([('weekoffs_id','=',self.employee_id.resource_calendar_id.id)],limit=1,order='create_date desc')
	# 		leave_id = self.env['hr.leave'].search([('employee_id','=',self.employee_id.id),('state','=','validate')],limit=1,order='create_date desc')
	# 		attendance_id = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id)],limit=1,order='create_date desc')
	# 		# if attendance_id:
	# 		# 	for attn in attendance_id:
	# 		# 		# for day in range(1, 31):
	# 		# 		# 	previous_date = (self.date_from - timedelta(day)).date()
	# 		# 			# if previous_date != attn.logged_date:
	# 		# 		print ("logged date")
	# 		# 		print(attn.logged_date)
	# 		# if weekoff_id:
	# 		# 	for weekoff in weekoff_id:
	# 		# 		print('weekoff')
	# 		# 		print(weekoff.weekoff_date)
	# 		if leave_id:
	# 			for leave in leave_id:
	# 				last_leave_date = leave.request_date_from
	# 				# # if leave.holiday_status_id.name == 'SL':
	# 				print('leave')
	# 				print(leave.request_date_from)
	# 		for line in self:
	# 			attendance_id = self.env['hr.attendance'].search([('employee_id','=',line.employee_id.id)])
	# 			if attendance_id:
	# 				for attn in attendance_id:
	# 					if attn.logged_date <= line.request_date_from and attn.logged_date >=last_leave_date:
	# 						print("hgfgfsgfs")
	# 						print (attn.logged_date)
	# 					else:
	# 						delta = line.request_date_from - last_leave_date
	# 						print('difference')
	# 						print(delta.days+1)

	@api.depends('request_date_from', 'request_date_to', 'employee_id')
	def _compute_number_of_days_display(self):
		res = super(HolidaysRequest, self)._compute_number_of_days_display()
		for record in self:
			start_date = record.date_from
			end_date = record.date_to
			if record.employee_id.sandwich and record.employee_id \
					and record.employee_id.resource_calendar_id.sandwich and record.employee_id:
				record.set_notification = record.employee_id.leave_notification

				leave_dates = []
				for leave_days in record.employee_id.resource_calendar_id.global_leave_ids:
					if leave_days.date_from.date() + timedelta(1) == leave_days.date_to.date():
						leave_dates.append(str(leave_days.date_to.date()))
					else:
						duration = (leave_days.date_to - leave_days.date_from).days + 1
						for single_date in (leave_days.date_from + timedelta(days) for days in range(duration)):
							leave_dates.append(str(single_date.date()))

				working_days = []
				for day in record.employee_id.resource_calendar_id.attendance_ids:
					if int(day.dayofweek) not in working_days:
						working_days.append(int(day.dayofweek))
				total_days = (end_date - start_date).days + 1

				check = 0
				for day in range(1, 31):
					next_date = (end_date + timedelta(day)).date()
					next_dates = str(next_date) in leave_dates or next_date.weekday() not in working_days
					if next_dates:
						check += 1
					else:
						break
				for day in range(1, 31):
					previous_date = (start_date - timedelta(day)).date()
					previous_dates = str(previous_date) in leave_dates or previous_date.weekday() not in working_days
					if previous_dates:
						check += 1
					else:
						break
				if start_date.date() != end_date.date():
					record.number_of_days = total_days + check
					record.number_of_days_display = record.number_of_days
				else:
					if record.number_of_days != 0:
						record.number_of_days += check
						record.number_of_days_display = record.number_of_days
			else:
				record.set_notification = False
				record.number_of_days = record._get_number_of_days(record.date_from, record.date_to, record.employee_id.id)
		return res


	@api.onchange('date_from', 'date_to', 'employee_id')
	def _onchange_leave_dates(self):
		last_leave_date = delta =0
		if self.date_from and self.date_to:
			leave_id = self.env['hr.leave'].search([('employee_id','=',self.employee_id.id),('state','=','validate')],limit=1,order='create_date desc')
			attendance_id = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id)],limit=1,order='create_date desc')
			if leave_id:
				for leave in leave_id:
					last_leave_date = leave.request_date_from
					print('Last leave')
					print(last_leave_date)
			if attendance_id:
				for attn in attendance_id:
					if attn.logged_date <= self.request_date_from and attn.logged_date >=last_leave_date:
						print("Login date")
						print (attn.logged_date)
						if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5
							# holiday.number_of_days_display = holiday.number_of_days - 0.5
						elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)
							# holiday.number_of_days_display = holiday.number_of_days
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 1
							# holiday.number_of_days_display = holiday.number_of_days - 1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5
							# holiday.number_of_days_display = holiday.number_of_days - 0.5
						else:
							self.number_of_days = 0
					else:
						delta = self.request_date_from - last_leave_date
						print('Diff')
						print(delta.days+1)
						if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5+delta.days
							# holiday.number_of_days_display = holiday.number_of_days - 0.5
						elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)+delta.days
							# holiday.number_of_days_display = holiday.number_of_days
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 1+delta.days
							# holiday.number_of_days_display = holiday.number_of_days - 1
						elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
							self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5+delta.days
							# holiday.number_of_days_display = holiday.number_of_days - 0.5
						else:
							self.number_of_days = 0+delta.days

			# if self.request_date_from_period == 'am' and self.request_date_to_period == 'am':
			# 	self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5
			# 	# holiday.number_of_days_display = holiday.number_of_days - 0.5
			# elif self.request_date_from_period == 'am' and self.request_date_to_period == 'pm':
			# 	self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)
			# 	# holiday.number_of_days_display = holiday.number_of_days
			# elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'am':
			# 	self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 1
			# 	# holiday.number_of_days_display = holiday.number_of_days - 1
			# elif self.request_date_from_period == 'pm' and self.request_date_to_period == 'pm':
			# 	self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - 0.5
			# 	# holiday.number_of_days_display = holiday.number_of_days - 0.5
			# else:
			# 	self.number_of_days = 0
				# holiday.number_of_days_display = holiday.number_of_days
		else:
			self.number_of_days = 0

	@api.onchange('request_date_from_period', 'request_date_to_period', 'request_hour_from', 'request_hour_to',
				  'request_date_from', 'request_date_to',
				  'employee_id')
	def _onchange_request_parameters(self):
		if not self.request_date_from:
			self.date_from = False
			return

		if self.request_unit_half or self.request_unit_hours:
			self.request_date_to = self.request_date_from

		if not self.request_date_to:
			self.date_to = False
			return

		domain = [('calendar_id', '=',
				   self.employee_id.resource_calendar_id.id or self.env.user.company_id.resource_calendar_id.id)]
		attendances = self.env['resource.calendar.attendance'].search(domain, order='dayofweek, day_period DESC')

		# find first attendance coming after first_day
		attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()),
							   attendances[0])
		# find last attendance coming before last_day
		attendance_to = next(
			(att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()),
			attendances[-1])

		# if self.request_date_from_period and not self.request_date_to_period:
		#     if self.request_date_from_period == 'am':
		#         hour_from = float_to_time(attendance_from.hour_from)
		#         hour_to = float_to_time(attendance_from.hour_to)
		#     else:
		#         hour_from = float_to_time(attendance_to.hour_from)
		#         hour_to = float_to_time(attendance_to.hour_to)
		# elif self.request_date_to_period and not self.request_date_from_period:
		#     if self.request_date_to_period == 'am':
		#         hour_from = float_to_time(attendance_from.hour_from)
		#         hour_to = float_to_time(attendance_from.hour_to)
		#     else:
		#         hour_from = float_to_time(attendance_to.hour_from)
		#         hour_to = float_to_time(attendance_to.hour_to)
		# elif self.request_unit_half:
		#     if self.request_date_from_period == 'am':
		#         hour_from = float_to_time(attendance_from.hour_from)
		#         hour_to = float_to_time(attendance_from.hour_to)
		#     else:
		#         hour_from = float_to_time(attendance_to.hour_from)
		#         hour_to = float_to_time(attendance_to.hour_to)
		if self.request_unit_hours:
			# This hack is related to the definition of the field, basically we convert
			# the negative integer into .5 floats
			hour_from = float_to_time(
				abs(self.request_hour_from) - 0.5 if self.request_hour_from < 0 else self.request_hour_from)
			hour_to = float_to_time(
				abs(self.request_hour_to) - 0.5 if self.request_hour_to < 0 else self.request_hour_to)
		elif self.request_unit_custom:
			hour_from = self.date_from.time()
			hour_to = self.date_to.time()
		else:
			hour_from = float_to_time(attendance_from.hour_from)
			hour_to = float_to_time(attendance_to.hour_to)

		tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC
		self.date_from = timezone(tz).localize(datetime.combine(self.request_date_from, hour_from)).astimezone(
			UTC).replace(tzinfo=None)
		self.date_to = timezone(tz).localize(datetime.combine(self.request_date_to, hour_to)).astimezone(UTC).replace(
			tzinfo=None)
		self._onchange_leave_dates()

	@api.multi
	def action_cancel(self):
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

	@api.multi
	def action_confirm(self):
		res = super(HolidaysRequest, self).action_confirm()
		template_id = self.env.ref('leave_custom.email_template_leave_request')
		template_id.send_mail(self.id, force_send=True)
		return res

	@api.multi
	def action_approve(self):
		res = super(HolidaysRequest, self).action_approve()
		template_id = self.env.ref('leave_custom.email_template_leave_approval')
		template_id.send_mail(self.id, force_send=True)
		return res

	@api.multi
	def action_refuse(self):
		current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		template_id = self.env.ref('leave_custom.email_template_leave_rejected')
		for holiday in self:
			if holiday.state not in ['confirm', 'validate', 'validate1']:
				raise UserError(_('Leave request must be confirmed or validated in order to refuse it.'))

			if holiday.state == 'validate1':
				template_id.send_mail(self.id, force_send=True)
				holiday.write({'state': 'refuse', 'first_approver_id': current_employee.id})
			else:
				template_id.send_mail(self.id, force_send=True)
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
		for employee in self.env['hr.employee'].search([('employment_status', '=', 'confirmed'), ('active', '=', True)]):
			if employee:
				el_leave = self.env['hr.leave.type'].search([('name', '=', 'EL')])
				if el_leave:
					el_id = self.env['hr.leave.allocation'].create({
						'name': 'EL Leave ' + str(datetime.now().month) + str(datetime.now().year),
						'holiday_status_id': el_leave.id,
						'number_of_days': el_leave.allocated_days,
						'holiday_type': 'employee',
						'employee_id': employee.id
					})
					if el_id:
						el_id.action_approve()
						if el_leave.validation_type == 'both':
							el_id.action_validate()
				sl_leave = self.env['hr.leave.type'].search([('name', '=', 'SL')])
				if sl_leave:
					sl_id = self.env['hr.leave.allocation'].create({
						'name': 'SL Leave ' + str(datetime.now().month) + str(datetime.now().year),
						'holiday_status_id': sl_leave.id,
						'number_of_days': sl_leave.allocated_days,
						'holiday_type': 'employee',
						'employee_id': employee.id
					})
					if sl_id:
						sl_id.action_approve()
						if sl_leave.validation_type == 'both':
							sl_id.action_validate()

	# Cron for Allocate PL after 1 year complete
	@api.model
	def _cron_allocate_pl_leave_year_complete(self):
		for employee in self.env['hr.employee'].search([('active', '=', True)]):
			allocation_id = self.env['hr.leave.allocation'].search([('holiday_status_id.name', '=', 'PL'),
																	('name', '=', 'PL Leave ' + str(datetime.now().year)),
																	('employee_id', '=', employee.id)])
			if allocation_id:
				continue
			else:
				if employee.joining_date:
					confirmation_date = employee.joining_date + relativedelta(years=1)
					if confirmation_date < date.today():
						pl_leave = self.env['hr.leave.type'].search([('name', '=', 'PL')])
						if pl_leave:
							pl_id = self.env['hr.leave.allocation'].create({
								'name': 'PL Leave ' + str(datetime.now().year),
								'holiday_status_id': pl_leave.id,
								'number_of_days': pl_leave.allocated_days,
								'holiday_type': 'employee',
								'employee_id': employee.id
							})
							if pl_id:
								pl_id.action_approve()
								if pl_leave.validation_type == 'both':
									pl_id.action_validate()
		# for employee in self.env['hr.employee'].search([('active', '=', True)]):
		#     if employee.joining_date:
		#         confirmation_date = employee.joining_date + relativedelta(years=1)
		#         if confirmation_date < date.today():
		#             pl_leave = self.env['hr.leave.type'].search([('name', '=', 'PL')])
		#             if pl_leave:
		#                 pl_id = self.env['hr.leave.allocation'].create({
		#                     'name': 'PL Leave ' + str(datetime.now().year),
		#                     'holiday_status_id': pl_leave.id,
		#                     'number_of_days': pl_leave.allocated_days,
		#                     'holiday_type': 'employee',
		#                     'employee_id': employee.id
		#                 })
		#                 if pl_id:
		#                     pl_id.action_approve()
		#                     if pl_leave.validation_type == 'both':
		#                         pl_id.action_validate()
