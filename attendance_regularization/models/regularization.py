from odoo import fields, api, models,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import datetime as dt

class Regular(models.Model):

	_name = 'attendance.regular'
	_rec_name = 'employee'
	_description = 'Approval Request'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'reg_date desc'

	@api.multi
	def _cron_create_checkout(self):
		attendance = self.env['hr.attendance'].search([('check_out', '=', False)])
		for line in attendance:
			if line.check_in:
				date = line.check_in
				line.check_out = date
				line.state = 'done'

	def _get_employee_id(self):
		employee_rec = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	req_date = fields.Date(string='Requested Date', default=fields.Date.today())
	reg_date = fields.Date(string='Regularized Date', required=True)
	reg_reason = fields.Text(string='Reason', required=True)
	employee = fields.Many2one('hr.employee', string="Employee", default=_get_employee_id, readonly=True, required=True)
	attendance_id = fields.Many2one('hr.attendance', string="Attendance", domain="([('employee_id','=',employee)])")
	check_in = fields.Datetime(string='Check In', related="attendance_id.check_in", store=True, track_visibility='onchange')
	check_out = fields.Datetime(string='Check Out', related="attendance_id.check_out", store=True, track_visibility='onchange')
	mail_check_in = fields.Datetime(string='Check In')
	mail_check_out = fields.Datetime(string='Check Out')
	state_select = fields.Selection([('draft', 'Draft'), ('requested', 'Requested'), ('reject', 'Rejected'),
									 ('approved', 'Approved')], default='draft', track_visibility='onchange', string='State')
	approver_remarks = fields.Char('Approver Remarks', track_visibility='onchange')
	name = fields.Char(default='New', copy=False, readonly=True, string="Name")
	start_latitude = fields.Char(string='Start Geo Latitude', related="attendance_id.start_latitude", store=True)
	start_longitude = fields.Float(string='Start Geo Longitude', digits=(16, 5), related="attendance_id.start_longitude", store=True)
	stop_latitude = fields.Char(string='Stop Geo Latitude', related="attendance_id.stop_latitude", store=True)
	stop_longitude = fields.Float(string='Stop Geo Longitude', digits=(16, 5), related="attendance_id.stop_longitude", store=True)

	@api.multi
	@api.onchange('reg_date')
	def onchange_reg_date(self):
		for regular in self:
			if regular.reg_date:
				# Temporary Commanded 7 days logic
				seven_days = regular.req_date + relativedelta(days=-7)
				if regular.reg_date < seven_days:
					raise UserError(_('Regularized date should be within 7 days'))
				else:
					today_date = datetime.date(datetime.today())
					regularize = self.env['attendance.regular'].sudo().search([('employee', '=', regular.employee.id),('reg_date', '=', regular.reg_date),('state_select', '!=', 'reject')])
					if regularize:
						for line in regularize:
							raise UserError(_('Already created regularization on this date'))
					elif regular.reg_date >= today_date:
						raise UserError(_('You are not able to regularize for Today and Future date'))
					atten = self.env['hr.attendance'].sudo().search([('employee_id', '=', regular.employee.id)])
					if atten:
						for rec in atten:
							if rec.check_in:
								date = rec.logged_date						
								if regular.reg_date == date and rec.check_in and rec.check_out:
									regular.attendance_id = rec.id
									val = rec.check_in + relativedelta (hours=5, minutes=30)
									final_time = val.time()
									cin = final_time.hour + (final_time.minute / 98.0)
									check_in = round(cin, 2)
									val2 = rec.check_out + relativedelta (hours=5, minutes=30)
									final_time2 = val2.time()
									cout = final_time2.hour + (final_time2.minute / 98.0)
									check_out = round(cout, 2)
									day = calendar.day_name[rec.check_out.weekday()]
									morn = day + ' ' + 'Morning'
									evng = day + ' ' + 'Evening'
									regularize = self.env['resource.calendar'].search([('company_id', '=', rec.env.user.company_id.id)], limit=1)
									line1 = regularize.attendance_ids.filtered(lambda x: x.name == morn)
									line2 = regularize.attendance_ids.filtered(lambda x: x.name == evng)
									if check_in and check_out:
										if line1.hour_from > check_in and line2.hour_to < check_out:
											raise UserError(_('Attendance is already created for this date'))
							elif not rec.check_in:
								regular.check_in = False
								regular.check_out = False

	###Hr Reminder/Notification
	def _get_employee_approver_id(self):
		employee_rec = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.lone_manager_id
	hr_reminder_approver_ids = fields.Many2many('hr.employee', string='Noti2 Approver',
												default=_get_employee_approver_id)

	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('attendance.regular')
		rec = super(Regular,self).create(vals)
		return rec

	# Unlink
	@api.multi
	def unlink(self):
		if self.filtered(lambda x:x.state_select not in 'draft'):
			raise UserError(_('You cannot delete the record which is not in draft !..'))
		return super(Regular, self).unlink()

	@api.multi
	def submit_reg(self):
		for record in self:
			current_employee = self.env.uid
			is_employee = self.employee.user_id.id
			sun_var = 'Sunday'
			day = calendar.day_name[record.reg_date.weekday()]
			if record.check_in:
				record.mail_check_in = record.check_in + relativedelta(hours=5, minutes=30)
				record.mail_check_out = record.check_out + relativedelta(hours=5, minutes=30)
			global_holiday = self.env['resource.calendar.leaves'].sudo().search([('date_holiday','!=',record.reg_date),('work_location_id', '=', record.employee.location_work_id.id)],limit=1)
			if sun_var == day:
				weekoff = self.env['resource.calendar.weekoffs'].sudo().search([('name', '=', 6)])
				if weekoff:
					raise UserError(_('The Requested day is Weekoff'))
			elif current_employee != is_employee:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))
			elif current_employee == is_employee:
				if record.reg_date:
					my_date = record.reg_date
					check_in = datetime.min.time()
					my_cin = datetime.combine(my_date, check_in) + relativedelta(hours=3, minutes=45)
					my_cout = my_cin + relativedelta(hours=8, minutes=15)
					# ========================= #
					att = self.env['hr.attendance'].sudo().search([('logged_date','=',record.reg_date),('employee_id','=',record.employee.id),('is_leave','=',True)])
					if att:
						raise UserError(_('You have applied full day leave on this date so you are not a allowed to Regularize !!.'))
					mor_leave = self.env['hr.attendance'].sudo().search([('logged_date','=',record.reg_date),('employee_id','=', record.employee.id),('morn_leave','=',True)])
					if mor_leave:
						if record.check_in == False and record.check_out == False:
							record.write({'check_in': my_cin + relativedelta(hours=3, minutes=45)})
							record.write({'check_out': my_cin + relativedelta(hours=8, minutes=15)})
						record.write({'state_select':'requested'})
						template_id = self.env.ref('attendance_regularization.email_template_request_attendance_regularized')
						template_id.sudo().send_mail(record.id, force_send=True)
						hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Attendance Regularization Request','employee_id': record.employee.id,
								'model_name': 'attendance.regular','approver_ids': [(6, 0, record.hr_reminder_approver_ids.ids)],'attendance_regular_id': record.id})
					evng_leave = self.env['hr.attendance'].sudo().search([('logged_date','=',record.reg_date),('employee_id','=', record.employee.id),('evng_leave','=',True)])
					if evng_leave:
						if record.check_in == False and record.check_out == False:
							record.write({'check_in': my_cin})
							record.write({'check_out': my_cin + relativedelta(hours=4, minutes=30)})
						record.write({'state_select': 'requested'})
						template_id = self.env.ref('attendance_regularization.email_template_request_attendance_regularized')
						template_id.sudo().send_mail(record.id, force_send=True)
						hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Attendance Regularization Request','employee_id': record.employee.id,
								'model_name': 'attendance.regular','approver_ids': [(6, 0, record.hr_reminder_approver_ids.ids)],'attendance_regular_id': record.id})
					# ========================= #
					else:
						if not mor_leave and not evng_leave:
							if record.check_in == False and record.check_out == False:
								record.write({'check_in': my_cin,'check_out':my_cout})
								record.mail_check_in = record.check_in + relativedelta(hours=5, minutes=30)
								record.mail_check_out = record.check_out + relativedelta(hours=5, minutes=30)
								record.write({'state_select': 'requested'})
								template_id = self.env.ref('attendance_regularization.email_template_request_attendance_regularized')
								template_id.sudo().send_mail(record.id, force_send=True)
								hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Attendance Rgularization Request', 'employee_id': record.employee.id,
									'model_name': 'attendance.regular','approver_ids': [(6, 0, record.hr_reminder_approver_ids.ids)],'attendance_regular_id': record.id})
							else:
								# if atten.reg_req == True:
								record.write({'state_select': 'requested'})
								template_id = self.env.ref('attendance_regularization.email_template_request_attendance_regularized')
								template_id.sudo().send_mail(record.id, force_send=True)
								hr_reminder = self.env['hr.reminder'].sudo().create({
								'name': 'Attendance Rgularization Request',
								'employee_id': record.employee.id, 'model_name': 'attendance.regular',
								'approver_ids': [(6, 0, record.hr_reminder_approver_ids.ids)],
								'attendance_regular_id': record.id
								})

	@api.multi
	def regular_approval(self):
		for vals in self:
			current_employee = vals.env.uid
			is_employee = vals.employee.sudo().lone_manager_id.user_id.id
			exist_rec = []
			if current_employee != is_employee:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))
			elif current_employee == is_employee:
				atttendance = self.env['hr.attendance'].sudo().search([('logged_date' ,'=', vals.reg_date),('employee_id' ,'=', vals.employee.id)])
				if atttendance:
					for attn in atttendance:
						attn.write({'reg_approved':True,'check_in':vals.check_in,'check_out':vals.check_out})
						vals.write({'state_select': 'approved'})
						template_id = self.env.ref('attendance_regularization.email_template_approval_attendance_regularized')
						template_id.sudo().send_mail(vals.id, force_send=True)
						hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Attendance Rgularization Approved','employee_id': vals.employee.id, 
						'model_name': 'attendance.regular','approver_ids': [(6, 0, vals.hr_reminder_approver_ids.ids)],'attendance_regular_id': vals.id})
				else:
					atte = self.env['hr.attendance'].create({'employee_id': vals.employee.id,'check_in' : vals.check_in,
														'check_out' : vals.check_out,'logged_date': vals.reg_date,'reg_approved' : True,
														'device_id' : vals.employee.device_id,'state' : 'done',})
					vals.write({'state_select': 'approved'})
					template_id = self.env.ref('attendance_regularization.email_template_approval_attendance_regularized')
					template_id.sudo().send_mail(vals.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({'name': 'Attendance Rgularization Approved','employee_id': vals.employee.id, 
					'model_name': 'attendance.regular','approver_ids': [(6, 0, vals.hr_reminder_approver_ids.ids)],'attendance_regular_id': vals.id})

	@api.multi
	def regular_rejection(self):
		current_employee = self.env.uid
		is_employee = self.employee.sudo().lone_manager_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		elif current_employee == is_employee:
			form_view = self.env.ref('attendance_regularization.form_regular_approver_remark_wizard')
			return {
				'name': "Approver Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'regular.approver.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'attendance_id': self.ids, 'is_reject': True
				}
			}
