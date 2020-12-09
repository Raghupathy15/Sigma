# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import requests
import json
import re
import collections
import geocoder
from odoo import models, fields, api, exceptions, _
from datetime import datetime, date, time, timedelta
import datetime as dt
import calendar
from pytz import timezone
import pytz
import dateutil.parser
from dateutil.relativedelta import relativedelta, MO
from odoo.exceptions import ValidationError, UserError
from odoo.tools import pycompat

class ResourceCalendarLeaves(models.Model):
	_inherit='resource.calendar.leaves'
	_order = 'date_from'
	date_holiday = fields.Date(string="Holiday Date", compute="compute_holiday_date")
	employee_id = fields.Many2one('hr.employee', string="Employee", compute="compute_employee_id")
	# holiday_id = fields.Many2one('resource.c', string="Holiday", compute="compute_holiday_date")

	@api.multi
	@api.depends('name')
	def compute_employee_id(self):
		for vals in self:
			for employee in self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)]):
				if employee:
					vals.employee_id = employee.id

	@api.multi
	@api.depends('date_from')
	def compute_holiday_date(self):
		for vals in self:
			if vals.date_from:
				vals.date_holiday = vals.date_from.date()

class HrAttendanceView(models.Model):
	_inherit='hr.attendance'

	# To Empty check in values
	@api.multi
	def name_get(self):
		result = []
		for attendance in self:
			if not attendance.check_out:
				result.append((attendance.id, _("%(empl_name)s  %(check_in)s") % {
					'empl_name': attendance.employee_id.name,
					'check_in': ''
				}))
			else:
				result.append((attendance.id, _("%(empl_name)s  %(check_in)s  %(check_out)s") % {
					'empl_name': attendance.employee_id.name,
					'check_in': '',
					'check_out': ''
				}))
		return result

	@api.multi
	@api.depends('check_in', 'check_out')
	def compute_actual_hours(self):
		for vals in self:
			if vals.check_in and vals.check_out:
				vals.worked_hours = (vals.check_out - vals.check_in)

	#fetched from standard
	work_hours = fields.Char(string="Work Hours",compute="fetch_work_hours")
	# worked_day = fields.Char(string="Worked Day",compute="fetch_worked_day")
	regular_count = fields.Integer(string='# RC', compute="_compute_attendance_regularize_count")
	logged_date = fields.Date(string="Date")
	monthly_permission = fields.Float(string="Monthly Permission Limit",related="employee_id.monthly_permission")
	casual_leave = fields.Float(string="Casual Leave",compute='fetch_casual_leaves',track_visibility='always')
	sick_leave = fields.Float(string="Sick Leave",compute='fetch_sick_leaves',track_visibility='always')
	paid_leave = fields.Float(string="Paid Leave",compute='fetch_paid_leaves',track_visibility='always')
	comp_off = fields.Float(string="Comp Off",compute='fetch_comp_off_leaves',track_visibility='always')
	loss_of_pay = fields.Float(string="Absent Days",track_visibility='always', compute='compute_reg_req')
	reg_req = fields.Boolean(string="Reg Reqd ?", compute="compute_reg_req")
	test_date = fields.Datetime(string="Check Date",default=fields.Datetime.now)
	reg_approved = fields.Boolean(string="Reg Approved")
	reg_rejected = fields.Boolean(string="Reg Rejected")
	reg_leave = fields.Boolean(string="Reg Leave", compute='compute_reg_req')
	worked_hours = fields.Char(string="Actual", compute="compute_actual_hours")
	differed_time = fields.Float(string = "Time Deviation")
	present_day_status = fields.Float (string="Present Status", compute='compute_reg_req')
	worked_time_in_sec = fields.Char(string="WTS")
	checked_in_within_time = fields.Boolean(string="Checked in within time")
	cal_time = fields.Float(string = "Time", compute='compute_reg_req')
	cal_out = fields.Float(string = "Time", compute='compute_reg_req')
	name = fields.Char(default='New', copy=False, readonly=True, string="Seq NO")
	start_time = fields.Datetime(string='Start Time')
	stop_time = fields.Datetime(string='Stop Time')
	start_latitude = fields.Char(string='Start Geo Latitude')
	start_longitude = fields.Float(string='Start Geo Longitude', digits=(16, 5))
	stop_latitude = fields.Char(string='Stop Geo Latitude')
	stop_longitude = fields.Float(string='Stop Geo Longitude', digits=(16, 5))
	device_id = fields.Char(string='Device ID')
	morn_session = fields.Selection([('p', 'P'),('a', 'A'),('l', 'L'),('h', 'H'),('wo', 'WO')], 
		default=('h'), string="Status",readonly=True, compute="compute_reg_req")
	evng_session = fields.Selection([('p', 'P'),('a', 'A'),('l', 'L'),('h', 'H'),('wo', 'WO')], 
		default=('h'), string="Status",readonly=True, compute="compute_reg_req")
	# Field added for calendar view
	attendance_status = fields.Char('Attendance status', compute="compute_attendance_status")
	regularize_status = fields.Char('Regularize status')
	state = fields.Selection([('draft', 'Draft'), ('started', 'Started'), ('done', 'Done')],default='draft',string="Stages")
	my_id = fields.Boolean(string="Mobile Attendance", compute='compute_attendance')
	is_today = fields.Boolean(string="Is Today", compute='compute_attendance')
	is_holiday = fields.Boolean(string="Is Holiday")
	is_absent = fields.Boolean(string="Is Absent")
	holiday_onch = fields.Float(string="Holiday Days")
	is_weekoff = fields.Boolean(string="Is Weekoff")
	week_off_onch = fields.Float(string="Weekoff Days")
	is_leave = fields.Boolean(string="Is Leave")
	morn_leave = fields.Boolean(string="Mrng Leave")
	evng_leave = fields.Boolean(string="Evng Leave")
	leave_days = fields.Float(string="Leave", compute="compute_reg_req")
	check_in = fields.Datetime(string="Check In",required=False,default=False)
	present_day_status_onch = fields.Float(string="Present Status")
	week_off = fields.Float(string="Weekoff")
	loss_of_pay_onch = fields.Float(string="Absent Days")
	leave_days_onch = fields.Float(string="Leave")
	holiday = fields.Float(string="Holiday")
	leave_id = fields.Many2one('hr.leave',string='Leave')
	holiday_status_id = fields.Many2one('hr.leave.type',string='Leaves Type',related='leave_id.holiday_status_id')
	holiday_status_onch_id = fields.Many2one('hr.leave.type',string='Leave Type')

	# @api.multi
	# def button_vals(self):
	# 	start_date = fields.Date.today().replace(day=1) - relativedelta(months=1)
	# 	end_date = date.today().replace(day=1) - timedelta(1)
	# 	today = date.today()
	# 	attendance = self.env['hr.attendance'].search([('logged_date','>=',start_date),('logged_date','<=',today)])
	# 	for rec in attendance:
	# 		if rec.present_day_status_onch != rec.present_day_status or rec.loss_of_pay_onch != rec.loss_of_pay or rec.leave_days_onch != rec.leave_days or rec.holiday != rec.holiday_onch or rec.week_off != rec.week_off_onch or rec.holiday_status_onch_id != rec.holiday_status_id or rec.regularize_status != rec.attendance_status:
	# 			print ('WWWWWWWWWWWWWWWW', today, start_date, rec.logged_date, rec)
	# 			rec.present_day_status_onch = rec.present_day_status
	# 			rec.loss_of_pay_onch = rec.loss_of_pay
	# 			rec.leave_days_onch = rec.leave_days
	# 			rec.holiday = rec.holiday_onch
	# 			rec.week_off = rec.week_off_onch
	# 			rec.regularize_status = rec.attendance_status

	@api.one
	def compute_attendance(self):
		for rec in self:
			current_date = fields.Date.today()
			if rec.logged_date == current_date:
				rec.is_today = True
			else:
				rec.is_today = False
			if rec.employee_id.attendance_type == 'mobile_app':
				rec.my_id = True

	# onchange for calendar view starts
	@api.depends('morn_session','evng_session')
	def compute_attendance_status(self):
		for val in self:
			if val.morn_session:
				var = str(val.morn_session) +" - "+ str(val.evng_session)
				val.attendance_status = var.upper()
	# onchange for calendar view ends

	@api.depends('check_in')
	def write_logged_date(self):
		for val in self.env['hr.attendance'].sudo().search([('logged_date', '=', False)]):
			if val.check_in:
				var = val.check_in.date()
				val.logged_date = var

	@api.multi
	def start_time_attendance(self):
		current_date = fields.Date.today()
		if self.logged_date == current_date:
			if self.attendance_type == 'mobile_app' and self.device_id:
				var = self.employee_id.device_id
				if self.device_id != var:
					raise ValidationError(_("The incoming Device ID is not matched with predefined Device ID"))
				else:	
					self.write({
						'check_in': dt.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
						'state': 'started'
						})
		else:
			raise ValidationError(_("You should start time for today"))

	@api.multi
	def stop_time_attendance(self):
		current_date = fields.Date.today()
		if self.logged_date == current_date:
			if self.attendance_type == 'mobile_app' and self.device_id:
				var = self.employee_id.device_id
				if self.device_id != var:
					raise ValidationError(_("The incoming Device ID is not matched with predefined Device ID"))
				else:	
					self.write({
						'check_out': dt.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
						'state': 'done'
						})
		else:
			raise ValidationError(_("You should stop time for today"))

	@api.multi
	def start_time_attendance_ios(self):
		current_date = fields.Date.today()
		if self.logged_date == current_date:
			if self.attendance_type == 'mobile_app' and self.device_id:
				var = self.employee_id.device_id
				if self.device_id != var:
					raise ValidationError(_("The incoming Device ID is not matched with predefined Device ID"))
				else:
					self.write({
						'check_in': dt.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
						'state': 'started'
					})
		else:
			raise ValidationError(_("You should start time for today"))

	@api.multi
	def stop_time_attendance_ios(self):
		current_date = fields.Date.today()
		if self.logged_date == current_date:
			if self.attendance_type == 'mobile_app' and self.device_id:
				var = self.employee_id.device_id
				if self.device_id != var:
					raise ValidationError(_("The incoming Device ID is not matched with predefined Device ID"))
				else:	
					self.write({
						'check_out': dt.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
						'state': 'done'
					})
		else:
			raise ValidationError(_("You should stop time for today"))

	@api.multi
	def open_start_time_map(self):
		for employee in self:
			url = "http://maps.google.com/maps?oi=map&q="
			if employee.start_latitude:
				url += str(employee.start_latitude)
			if employee.start_longitude:
				url += ',' + str(employee.start_longitude)
		return {
			'type': 'ir.actions.act_url',
			'target': 'new',
			'url': url
		}

	@api.multi
	def open_stop_time_map(self):
		for employee in self:
			url = "http://maps.google.com/maps?oi=map&q="
			if employee.stop_latitude:
				url += str(employee.stop_latitude)
			if employee.stop_longitude:
				url += ',' + str(employee.stop_longitude)
		return {
			'type': 'ir.actions.act_url',
			'target': 'new',
			'url': url
		}

	@api.multi
	@api.depends('check_in', 'check_out', 'reg_req', 'present_day_status', 'reg_approved','is_holiday')
	def compute_reg_req(self):
		for vals in self:
			# To create record in attendance - start
			
			if vals.is_holiday == True:
				vals.morn_session = 'h'
				vals.evng_session = 'h'
				vals.holiday_onch = 1
				vals.week_off_onch = 0
				vals.leave_days = 0
			elif vals.is_weekoff == True:
				vals.morn_session = 'wo'
				vals.evng_session = 'wo'
				vals.week_off_onch = 1
				vals.holiday_onch = 0
				vals.leave_days = 0
			elif vals.is_leave == True:
				leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
				vals.leave_id = leave.id
				vals.morn_session = 'l'
				vals.evng_session = 'l'
				vals.leave_days = 1
				vals.week_off_onch = 0
				vals.holiday_onch = 0
			elif vals.morn_leave == True and vals.evng_leave == False:
				leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
				vals.leave_id = leave.id
				vals.morn_session = 'l'
				vals.evng_session = 'a'
				vals.leave_days = 0.5
				vals.loss_of_pay = 0.5
				vals.week_off_onch = 0
				vals.holiday_onch = 0
			elif vals.evng_leave == True and vals.morn_leave == False:
				leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
				vals.leave_id = leave.id
				vals.morn_session = 'a'
				vals.evng_session = 'l'
				vals.leave_days = 0.5
				vals.loss_of_pay = 0.5
				vals.week_off_onch = 0
				vals.holiday_onch = 0
			elif vals.evng_leave == True and vals.morn_leave == True:
				leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
				vals.leave_id = leave.id
				vals.morn_session = 'l'
				vals.evng_session = 'l'
				vals.leave_days = 1
				vals.loss_of_pay = 0
				vals.week_off_onch = 0
				vals.holiday_onch = 0
			elif vals.is_absent == True or (not vals.check_in and not vals.check_out):
				vals.morn_session = 'a'
				vals.evng_session = 'a'
				vals.leave_days = 0
				vals.loss_of_pay = 1
				vals.week_off_onch = 0
				vals.holiday_onch = 0
			for holiday in self.env['resource.calendar.leaves'].sudo().search([('work_location_id','=',vals.employee_id.location_work_id.id),('company_id','=',vals.employee_id.company_id.id)]):
				if holiday.date_holiday == vals.logged_date:
					vals.morn_session = 'h'
					vals.evng_session = 'h'
					vals.holiday_onch = 1
					vals.week_off_onch = 0
					vals.leave_days = 0
			data = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate')])
			if data:
				for leave in data:
					if leave.request_date_from and leave.request_date_to and vals.logged_date:
						if (vals.logged_date >= leave.request_date_from) and (vals.logged_date <= leave.request_date_to):
							if leave.request_date_from_period == 'am' and leave.request_date_to_period == 'pm':
								leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
								vals.leave_id = leave.id
								vals.morn_session = 'l'
								vals.evng_session = 'l'
								vals.leave_days = 1
								vals.present_day_status = 0
								vals.week_off_onch = 0
								vals.holiday_onch = 0
							elif not vals.morn_session == 'l' and not vals.evng_session == 'l':
								if leave.request_date_from_period == 'am':
									leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
									vals.leave_id = leave.id
									if vals.check_in and vals.check_out:
										vals.morn_session = 'l'
										vals.evng_session = 'p'
										vals.leave_days = 0.5
										vals.present_day_status = 0.5
										vals.loss_of_pay = 0
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
									else:
										vals.morn_session = 'l'
										vals.evng_session = 'a'
										vals.leave_days = 0.5
										vals.present_day_status = 0
										vals.loss_of_pay = 0.5
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
								if leave.request_date_from_period == 'pm':
									leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
									vals.leave_id = leave.id
									if vals.check_in and vals.check_out:
										vals.morn_session = 'p'
										vals.evng_session = 'l'
										vals.leave_days = 0.5
										vals.present_day_status = 0.5
										vals.loss_of_pay = 0
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
									else:
										vals.morn_session = 'a'
										vals.evng_session = 'l'
										vals.leave_days = 0.5
										vals.present_day_status = 0
										vals.loss_of_pay = 0.5
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
								if leave.request_date_to_period == 'am':
									leave = self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.id),('state','=','validate'),('request_date_from','<=',vals.logged_date),('request_date_to','>=',vals.logged_date)],limit=1)
									vals.leave_id = leave.id
									if vals.check_in and vals.check_out:
										vals.morn_session = 'l'
										vals.evng_session = 'p'
										vals.leave_days = 0.5
										vals.present_day_status = 0.5
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
									else:
										vals.morn_session = 'l'
										vals.evng_session = 'a'
										vals.leave_days = 0.5
										vals.present_day_status = 0
										vals.loss_of_pay = 0.5
										vals.week_off_onch = 0
										vals.holiday_onch = 0
										vals.is_leave = True
			# To create record in attendance - end
			if vals.check_in and vals.check_out and vals.is_holiday == False and vals.is_weekoff == False:
				check_in = time_val = tar = 0 
				check_out = time_cout = tar_cout = 0
				today = vals.check_in
				cout = vals.check_out
				tz_name = self.env.user.tz
				if tz_name:
					today_utc = pytz.timezone('UTC').localize(today, is_dst=False)  # UTC = no DST
					cout_utc = pytz.timezone('UTC').localize(cout, is_dst=False)  # UTC = no DST
					context_today = today_utc.astimezone(pytz.timezone(tz_name))
					context_cout = cout_utc.astimezone(pytz.timezone(tz_name))
					time_val = context_today.time()
					time_cout = context_cout.time()
					tar = time_val.hour + (time_val.minute / 98.0)
					tar_cout = time_cout.hour + (time_cout.minute / 98.0)
					vals.cal_time = (round(tar, 2))
					vals.cal_out = (round(tar_cout, 2))
					day = calendar.day_name[vals.logged_date.weekday()]
					morn = day + ' ' + 'Morning'
					evng = day + ' ' + 'Evening'
					regularize = self.env['resource.calendar'].search([('company_id', '=', vals.env.user.company_id.id)], limit=1)
					line1 = regularize.attendance_ids.filtered(lambda x: x.name == morn)
					line2 = regularize.attendance_ids.filtered(lambda x: x.name == evng)
					break_time =  line2.hour_from + 1
					morn_break_time = line2.hour_from - 2
					# Attendance status is l and a
					if (morn_break_time < vals.cal_time and line2.hour_to > vals.cal_out) or (line2.hour_from < vals.cal_time and line2.hour_to < vals.cal_out):
						vals.reg_req = True
						if not vals.morn_session == 'l' and not vals.evng_session == 'l':
							vals.morn_session = 'a'
							vals.evng_session = 'a'
							vals.leave_days = 0
							vals.loss_of_pay = 1
							vals.week_off_onch = 0
							vals.holiday_onch = 0
						elif vals.morn_session == 'l':
							vals.morn_session = 'l'
							vals.evng_session = 'a'
							vals.leave_days = 0.5
							vals.loss_of_pay = 0.5
							vals.week_off_onch = 0
							vals.holiday_onch = 0
						elif vals.evng_session == 'l':
							vals.morn_session = 'a'
							vals.evng_session = 'l'
							vals.leave_days = 0.5
							vals.loss_of_pay = 0.5
							vals.week_off_onch = 0
							vals.holiday_onch = 0
					# Attendance status is l and p
					elif morn_break_time < vals.cal_time and line2.hour_to < vals.cal_out:
						vals.reg_req = True
						if not vals.morn_session == 'l':
							vals.morn_session = 'a'
							vals.evng_session = 'p'
							vals.present_day_status = 0.5
							vals.loss_of_pay = 0.5
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 0
						elif vals.morn_session == 'l':
							vals.morn_session = 'l'
							vals.evng_session = 'p'
							vals.present_day_status = 0.5
							vals.loss_of_pay = 0
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 0.5
					# Attendance status is a and l
					elif (line1.hour_from <= vals.cal_time and break_time >= vals.cal_out) or (line1.hour_from >= vals.cal_time and line1.hour_to >= vals.cal_out):
						vals.reg_req = True
						if not vals.morn_session == 'l':
							vals.morn_session = 'a'
						if not vals.evng_session == 'l':
							vals.evng_session = 'a'
						vals.present_day_status = 0
						vals.loss_of_pay = 1
						vals.week_off_onch = 0
						vals.holiday_onch = 0
						vals.leave_days = 0
					# Attendance status is a and a
					elif line1.hour_from <= vals.cal_time and line2.hour_to >= vals.cal_out:
						vals.reg_req = True
						if not vals.morn_session == 'l' and not vals.evng_session == 'l':
							vals.morn_session = 'a'
							vals.evng_session = 'a'
							vals.present_day_status = 0
							vals.loss_of_pay = 1
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 0
						if vals.morn_session == 'l' and vals.evng_session == 'l':
							vals.morn_session = 'l'
							vals.evng_session = 'l'
							vals.present_day_status = 0
							vals.loss_of_pay = 0
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 1
					# Attendance status is a and p
					elif line1.hour_from <= vals.cal_time and line2.hour_to <= vals.cal_out:
						vals.reg_req = True
						if not vals.morn_session == 'l':
							vals.morn_session = 'a'
						if not vals.evng_session == 'l':
							vals.evng_session = 'p'
						vals.present_day_status = 0.5
						vals.loss_of_pay = 0.5
						vals.week_off_onch = 0
						vals.holiday_onch = 0
						vals.leave_days = 0
					# Attendance status is p and l
					elif line1.hour_from >= vals.cal_time and break_time >= vals.cal_out:
						vals.reg_req = True
						if not vals.evng_session == 'l':
							vals.morn_session = 'p'
							vals.evng_session = 'a'
							vals.present_day_status = 0.5
							vals.loss_of_pay = 0.5
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 0
						elif vals.evng_session == 'l':
							vals.morn_session = 'p'
							vals.evng_session = 'l'
							vals.present_day_status = 0.5
							vals.loss_of_pay = 0
							vals.week_off_onch = 0
							vals.holiday_onch = 0
							vals.leave_days = 0.5
					# Attendance status is p and a
					elif line1.hour_from >= vals.cal_time and line2.hour_to > vals.cal_out:
						vals.reg_req = True
						if not vals.morn_session == 'l':
							vals.morn_session = 'p'
						if not vals.evng_session == 'l':
							vals.evng_session = 'a'
						vals.present_day_status = 0.5
						vals.loss_of_pay = 0.5
						vals.week_off_onch = 0
						vals.holiday_onch = 0
						vals.leave_days = 0
					# Attendance status is p and p
					elif line1.hour_from >= vals.cal_time and line2.hour_to <= vals.cal_out and vals.is_leave == False:
						vals.reg_req = False
						vals.morn_session = 'p'
						vals.evng_session = 'p'
						vals.present_day_status = 1
						vals.loss_of_pay = 0
						vals.week_off_onch = 0
						vals.holiday_onch = 0
						vals.leave_days = 0
				if vals.reg_req == True and vals.reg_approved == False:
					if (vals.morn_session == 'p' and vals.evng_session == 'a') or (vals.morn_session == 'a' and vals.evng_session == 'p') or (vals.morn_session == 'a' and vals.evng_session == 'a'):
						for leave in self.env['hr.leave'].sudo().search([('employee_id', '=', vals.employee_id.id),('state', '=', 'validate')]):
							if (vals.check_in.date() == leave.request_date_from) or (vals.check_in.date() == leave.request_date_to):
								if (vals.check_in.date() >= leave.request_date_from) and (vals.check_in.date() <= leave.request_date_to):
									if (vals.morn_session == 'p' and vals.evng_session == 'a'):
										vals.present_day_status = 0.5
										vals.loss_of_pay = 0
										vals.leave_days = 0.5
										vals.morn_session = 'p'
										vals.evng_session = 'l'
										vals.reg_leave = True
										vals.week_off_onch = 0
										vals.holiday_onch = 0
									elif (vals.morn_session == 'a' and vals.evng_session == 'p'):
										vals.present_day_status = 0.5
										vals.loss_of_pay = 0
										vals.leave_days = 0.5
										vals.morn_session = 'l'
										vals.evng_session = 'p'
										vals.reg_leave = True
										vals.week_off_onch = 0
										vals.holiday_onch = 0
				elif vals.reg_req == True:
					if (vals.morn_session == 'p' and vals.evng_session == 'a') or (vals.morn_session == 'a' and vals.evng_session == 'p') or (vals.morn_session == 'a' and vals.evng_session == 'a'):
						vals.present_day_status = 1
						vals.loss_of_pay = 0
						vals.holiday_onch = 0
						vals.leave_days = 0
						vals.week_off_onch = 0
						if not vals.morn_session == 'l':
							vals.morn_session = 'p'
						if not vals.evng_session == 'l':
							vals.evng_session = 'p'
					elif (vals.morn_session == 'a' and vals.evng_session == 'l'):
						vals.present_day_status = 0.5
						vals.loss_of_pay = 0
						vals.holiday_onch = 0
						vals.leave_days = 0.5
						vals.week_off_onch = 0
						vals.morn_session = 'p'
						vals.evng_session = 'l'
					elif (vals.morn_session == 'l' and vals.evng_session == 'a'):
						vals.present_day_status = 0.5
						vals.loss_of_pay = 0
						vals.holiday_onch = 0
						vals.leave_days = 0.5
						vals.week_off_onch = 0
						vals.morn_session = 'l'
						vals.evng_session = 'p'

									
									
							

	# @api.model
	# def create(self,vals):
	# 	res = super(HrAttendanceView,self).create(vals)
	# 	if res:
	# 		if res.attendance_type == 'mobile_app':
	# 			if not res.device_id:
	# 				raise ValidationError(_("The Device ID Should be valid"))
	# 	vals['name'] = self.env['ir.sequence'].next_by_code('hr.attendance')
	# 	return res

	@api.multi
	def action_view_regular_req(self):
		self.ensure_one()
		action = self.env.ref('attendance_regularization.action_view_regularization1').read()[0]
		attendance_regularize = []
		regularize = self.env['attendance.regular'].search([('employee', '=', self.employee_id.id)], order='id desc')
		for count in regularize:
			attendance_regularize.append(count.id)
		if len(attendance_regularize) >= 1:
			action['domain'] = [('id', 'in', attendance_regularize)]
			return action
		else:
			action['domain'] = [('id', 'in', [])]
			return action

	def _compute_attendance_regularize_count(self):
		for vals in self:
			attendance_regularize = []
			quart_search = self.env['attendance.regular'].search([('employee', '=', self.employee_id.id)], order='id desc')
			for count in quart_search:
				attendance_regularize.append(count.id)
			vals.regular_count = len(attendance_regularize)

	@api.multi
	@api.depends('employee_id','logged_date','check_in','check_out')
	def fetch_casual_leaves(self):
		for line in self:
			casual_leave = 0
			hr_leave = self.env['hr.leave'].search([('employee_id','=',line.employee_id.id)])
			if hr_leave:
				for leaves in hr_leave:
					if line.logged_date:
						if line.logged_date >= leaves.request_date_from and line.logged_date <= leaves.request_date_to:
							if leaves.holiday_status_id.code == 'CL' and leaves.state == 'validate':
								casual_leave = casual_leave + leaves.number_of_days_display
				line.casual_leave = casual_leave

	@api.multi
	@api.depends('employee_id','logged_date','check_in','check_out')
	def fetch_sick_leaves(self):
		for line in self:
			sick_leave = 0
			hr_leave = self.env['hr.leave'].search([('employee_id','=',line.employee_id.id)])
			if hr_leave:
				for leaves in hr_leave:
					if line.logged_date:
						if line.logged_date >= leaves.request_date_from and line.logged_date <= leaves.request_date_to:
							if leaves.holiday_status_id.code == 'SL' and leaves.state == 'validate':
								sick_leave = sick_leave + leaves.number_of_days_display
				line.sick_leave = sick_leave

	@api.multi
	@api.depends('employee_id','logged_date','check_in','check_out')
	def fetch_comp_off_leaves(self):
		for line in self:
			comp_off = 0
			hr_leave = self.env['hr.leave'].search([('employee_id','=',line.employee_id.id)])
			if hr_leave:
				for leaves in hr_leave:
					if line.logged_date:
						if line.logged_date >= leaves.request_date_from and line.logged_date <= leaves.request_date_to:
							if leaves.holiday_status_id.code == 'COMP' and leaves.state == 'validate':
								comp_off = comp_off + leaves.number_of_days_display
				line.comp_off = comp_off

	@api.multi
	@api.depends('employee_id','logged_date','check_in','check_out')
	def fetch_paid_leaves(self):
		for line in self:
			paid_leave = sick_leave = casual_leave = comp_off = loss_of_pay = 0
			hr_leave = self.env['hr.leave'].search([('employee_id','=',line.employee_id.id)])
			if hr_leave:
				for leaves in hr_leave:
					if line.logged_date:
						if line.logged_date >= leaves.request_date_from and line.logged_date <= leaves.request_date_to:
							if leaves.holiday_status_id.code == 'PL' and leaves.state == 'validate':
								paid_leave = paid_leave + leaves.number_of_days_display
				line.paid_leave = paid_leave

	@api.multi
	@api.depends('employee_id')
	def fetch_work_hours(self):
		for line in self:
			if line.employee_id:
				line.work_hours = line.employee_id.resource_calendar_id.hours_per_day

	@api.multi
	@api.depends('check_out','check_in')
	def fetch_worked_hours(self):
		check_in = check_out = 0
		#fetch check in and check out time in seconds
		actual_check_in = actual_check_out = total_actual_seconds =0
		actual_in_str = actual_in_hour = actual_in_min = actual_in_sec = actual_in_time_in_sec =0
		#Minimum hours to be worked
		min_hours_to_work = min_hours_to_work_in_seconds =0
		min_str = min_hour = min_min = min_sec = min_time_in_sec =0

		#worked time onveting into seconds for comparision
		worked_time = worked_time_in_seconds =0
		work_str = work_hour = work_work = work_sec = work_time_in_sec =0

		#Total seconds to work. defined in master
		total_sec_to_be_worked = 0
		#
		early_check_in_from = early_check_in_to = 0
		#for early login and late logout
		early_check_in_time = in_time = out_time = 0
		early_str = early_hour = early_min = early_sec = early_time_in_sec =0
		time_worked = 0
		for line in self:
			if line.check_in and line.check_out and line.check_out > line.check_in:
				check_in = datetime.strptime(str(line.check_in), '%Y-%m-%d %H:%M:%S')
				check_out = datetime.strptime(str(line.check_out),'%Y-%m-%d %H:%M:%S')
				#difference of check in and check out
				time_worked = datetime.strptime(str(check_out.time()),'%H:%M:%S') - datetime.strptime(str(check_in.time()),'%H:%M:%S')

				
				#difference of check in and check out to calculate the total hours worked
				line.worked_hours = time_worked

				worked_time = time_worked
				work_str = str(worked_time)
				work_hour,work_min,work_sec = work_str.split(':')
				worked_time_in_seconds = int(work_hour)* 3600 + int(work_min) *60 + int(work_sec)
				line.worked_time_in_sec = worked_time_in_seconds

				early_check_in_from = '30600' #8:30:00
				# early_check_in_to = '34200' #9:30:00 
				early_check_in_to = '33300' #9:15:00 900+32400


				#converting the check_in time to seconds
				actual_check_in = datetime.strptime(str(check_in.time()),'%H:%M:%S')
				actual_in_str = str(actual_check_in)[11:19]
				actual_in_hour,actual_in_min,actual_in_sec = actual_in_str.split(':')
				actual_in_time_in_sec = int(actual_in_hour)* 3600 + int(actual_in_min) *60 + int(actual_in_sec)
				total_actual_seconds = str(int(actual_in_time_in_sec) + 19800)

				

				#condition to check the login regularization
				early_check_in_time = '13:30:00'
				early_str = str(early_check_in_time)
				early_hour,early_min,early_sec = early_str.split(':')
				early_time_in_sec = int(early_hour)* 3600 + int(early_min) *60 + int(early_sec)
				

				#condition to check the minimum hours to work and convert in seconds
				min_hours_to_work = '4:30:00'
				min_str = str(min_hours_to_work)
				min_hour,min_min,min_sec = min_str.split(':')
				min_time_in_sec = int(min_hour)* 3600 + int(min_min) *60 + int(min_sec)
				# line.worked_time_in_sec = min_time_in_sec


				#check for late login and apply for regularization
				if int(total_actual_seconds) > int(early_check_in_to):
					line.checked_in_within_time = False
				else:
					line.checked_in_within_time = True

				#enable regularization request
				if line.checked_in_within_time == False:
					#complete 9 hours
					total_sec_to_be_worked = '32400'
					#condition works only login made after 9.30 and before 13.30
					if int(total_actual_seconds) > int(early_check_in_to) and int(total_actual_seconds) < int(early_time_in_sec):
						#if total worked time > 4.30 and time worked < 9.00(total to work)
						if int(worked_time_in_seconds) > int(min_time_in_sec):
							if int(worked_time_in_seconds) < int(total_sec_to_be_worked):
								#worked time is less than the time to be worked and reg is approved
								if not line.paid_leave and not line.casual_leave and not line.sick_leave and not line.comp_off:
									line.reg_req = True
								if line.reg_approved == True:
									line.present_day_status = 1
								else:
									line.present_day_status = 0.5
									#check for leaves applied after reg rejected
									if not line.paid_leave and not line.casual_leave and not line.sick_leave and not line.comp_off:
										line.loss_of_pay = 0.5
						else:
							line.loss_of_pay = 1
					else:
						line.present_day_status = 0
						if int(total_actual_seconds) > int(early_time_in_sec):
							if not line.paid_leave and not line.casual_leave and not line.sick_leave and not line.comp_off:
								line.loss_of_pay = 1
							else:
								line.loss_of_pay = 0.5
						line.reg_req = False
				else:
					total_sec_to_be_worked = '32400'
					#condition works only if the checkin is made within time 9.00 < 9.30
					if int(total_actual_seconds) < int(early_check_in_to) and int(total_actual_seconds) < int(early_time_in_sec):
						#if total worked time > 4.30 and time worked < 9.00(total to work)
						if int(worked_time_in_seconds) > int(min_time_in_sec):
							if int(worked_time_in_seconds) < int(total_sec_to_be_worked):
								#worked time is less than the time to be worked and reg is approved
								if not line.paid_leave and not line.casual_leave and not line.sick_leave and not line.comp_off:
									line.reg_req = True
								if line.reg_approved == True:
									line.present_day_status = 1
								else:
									line.present_day_status = 0.5
									#check for leaves applied after reg rejected
									if not line.paid_leave and not line.casual_leave and not line.sick_leave and not line.comp_off:
										line.loss_of_pay = 0.5
							else:
								line.present_day_status = 1
					else:
						line.reg_req =False

	@api.multi
	@api.depends('check_in')
	def action_old_fetch_rec(self):
		reg = self.env['attendance.regular'].sudo().search([('state_select', '=', 'approved')])
		if reg:
			for vals in reg:
				# if vals.employee.attendance_type == 'rfid':
				var = self.env['hr.attendance'].sudo().search([('employee_id', '=', vals.employee.id),('logged_date', '=', vals.reg_date)])
				if var:
					for line in var:
						line.reg_approved = True
				elif not var:
					my_date = vals.reg_date
					check_in = datetime.min.time()
					my_cin = datetime.combine(my_date, check_in) + relativedelta(hours=3, minutes=45)
					my_cout = my_cin + relativedelta(hours=8, minutes=15)
					atte = self.env['hr.attendance'].sudo().create({
					'employee_id': vals.employee.id,
					'check_in' : my_cin,
					'check_out' : my_cout,
					'logged_date': vals.reg_date,
					'reg_approved' : True,
					'device_id' : vals.employee.device_id,
					'state' : 'done',
					})


	@api.constrains('check_in', 'check_out', 'employee_id')
	def _check_validity(self):
		""" Verifies the validity of the attendance record compared to the others from the same employee.
			For the same employee we must have :
				* maximum 1 "open" attendance record (without check_out)
				* no overlapping time slices with previous employee records
		"""
		for attendance in self:
			# we take the latest attendance before our check_in time and check it doesn't overlap with ours
			last_attendance_before_check_in = self.env['hr.attendance'].search([
				('employee_id', '=', attendance.employee_id.id),
				('check_in', '<=', attendance.check_in),
				('id', '!=', attendance.id),
			], order='check_in desc', limit=1)
			# if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
			#     raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
			#         'empl_name': attendance.employee_id.name,
			#         'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
			#     })

			if not attendance.check_out:
				# if our attendance is "open" (no check_out), we verify there is no other "open" attendance
				no_check_out_attendances = self.env['hr.attendance'].search([
					('employee_id', '=', attendance.employee_id.id),
					('check_out', '=', False),
					('id', '!=', attendance.id),
				], order='check_in desc', limit=1)
				# if no_check_out_attendances:
				#     raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
				#         'empl_name': attendance.employee_id.name,
				#         'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
				#     })
			else:
				# we verify that the latest attendance with check_in time before our check_out time
				# is the same as the one before our check_in time computed before, otherwise it overlaps
				last_attendance_before_check_out = self.env['hr.attendance'].search([
					('employee_id', '=', attendance.employee_id.id),
					('check_in', '<', attendance.check_out),
					('id', '!=', attendance.id),
				], order='check_in desc', limit=1)
				# if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
				#     raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
				#         'empl_name': attendance.employee_id.name,
				#         'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
				#     })
