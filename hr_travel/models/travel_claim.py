# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, date, timedelta

class HrTravelClaim(models.Model):
	_name = 'hr.travel.claim'
	_description = 'Travel Claim'
	_inherit = ['mail.thread']
	_order = 'id desc'

	@api.multi
	@api.onchange('conveyance_ids.amount', 'local_conveyance', 'actual_accommodation', 'acc_eligibility')
	def onchange_conveyance(self):
		amount = 0.0
		for line in self.conveyance_ids:
			amount += line.amount
			self.local_conveyance = round(amount, 2)
		if self.actual_accommodation > self.acc_eligibility:
			self.is_justify = True
		else:
			self.is_justify = False

	@api.multi
	@api.depends('conveyance_ids.amount', 'actual_accommodation', 'food_actual', 'local_conveyance', 'acc_eligibility', 'food_eligibility','total_eligible_cost', 'other_expenses')
	def compute_total(self):
		for vals in self:
			amount = 0.0
			for line in vals.conveyance_ids:
				amount += line.amount
			vals.local_conveyance = round(amount, 2)
			if vals.date_to:
				if vals.acc_eligibility or vals.food_eligibility:
					vals.total_eligible_cost = vals.acc_eligibility + vals.food_eligibility
				if vals.actual_accommodation or vals.food_actual or vals.local_conveyance or vals.other_expenses:
					vals.actual_cost = vals.actual_accommodation + vals.food_actual + vals.local_conveyance + vals.other_expenses
				if vals.travel_advance or vals.additional_advance:
					vals.total_advance = vals.travel_advance + vals.additional_advance
				if vals.total_advance or vals.actual_cost:
					vals.balance_amount = vals.actual_cost - vals.total_advance
			

	travel_request_id = fields.Many2one('hr.travel', string='Travel Request')
	travel_admin_id = fields.Many2one('hr.travel.admin', string='Travel Request')
	state = fields.Selection([('draft', 'Draft'),('approver1', 'Approver 1'),('hod', 'HOD'),('director', 'Director'),
		('accounts', 'Accounts'),('acc_head', 'Accounts Head'), ('approved', 'Approved'),('rejected', 'Rejected'),('cancelled', 'Cancelled')],
							 string='Status', default='draft',track_visibility='onchange')
	name = fields.Char(default='New', copy=False, readonly=True, string="Name")
	date = fields.Date(readonly=True, default=fields.Date.context_today, string="Created Date")
	employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
	designation_id = fields.Many2one('employee.designation', string='Designation', related="employee_id.designation_id")
	approver1_id = fields.Many2one('hr.employee', string='Approver 1', related="employee_id.lone_manager_id")
	approver2_id = fields.Many2one('hr.employee', string='Approver 2', related="employee_id.ltwo_manager_id")
	hod_id = fields.Many2one('hr.employee', string='HOD', related="employee_id.hod_id")
	job_id = fields.Many2one('hr.job', string='Designation',related="employee_id.job_id")
	department_id = fields.Many2one('hr.department', string='Department',related="employee_id.department_id")
	from_location_id = fields.Many2one('location.master', string='From Location')
	to_location_id = fields.Many2one('location.master', string='To Location')
	travel_type = fields.Selection([('one_way', 'One Way'), ('round_trip', 'Round Trip'), ('return', 'Return')],track_visibility='onchange')
	travel_mode_id = fields.Many2one('travel.mode.master','Travel Mode',track_visibility='onchange', related="travel_admin_id.travel_mode_id")	
	project_ref_id = fields.Many2one('project.project', string='Project Name')
	date_from = fields.Date(string="Perdiem Date", readonly=True)
	date_to = fields.Date(string="End Date")
	no_of_days = fields.Integer(string="Number of Days",track_visibility='onchange', related="travel_admin_id.no_of_days")
	departure_date = fields.Date(string="Departure Date")
	acc_eligibility = fields.Float(string="Accommodation-Eligibility",track_visibility='onchange', digits=(16, 0), compute="compute_amount")
	food_eligibility = fields.Float(string="Food-Eligibility",track_visibility='onchange', digits=(16, 0), compute="compute_amount")
	food_actual = fields.Float(string="Food-Actual",track_visibility='onchange', digits=(16, 0))
	accommodation = fields.Selection([('guest_house', 'Guest House'), ('hotel', 'Hotel'), ('self', 'Self')], string='Accommodation')
	hotel_booking = fields.Selection([('self', 'Self'), ('admin', 'Travel Admin')], string='Hotel Booking by')
	local_conveyance = fields.Float(string="Local Conveyance",track_visibility='onchange', digits=(16, 0), compute='compute_total')
	other_expenses = fields.Float(string="Other Expenses",track_visibility='onchange', digits=(16, 0))
	other_justification = fields.Char('Other Justification')
	actual_accommodation = fields.Float(string="Accommodation-Actual",track_visibility='onchange', digits=(16, 0))
	actual_cost = fields.Float(string="Total Expenses", compute="compute_total",track_visibility='onchange', digits=(16, 0))
	onward_ticket_cost = fields.Float('Onward Ticket Cost',track_visibility='onchange', digits=(16, 0))
	return_ticket_cost = fields.Float('Return Ticket Cost',track_visibility='onchange', digits=(16, 0), related="travel_admin_id.return_ticket_cost")
	return_travel_mode_id = fields.Many2one('travel.mode.master','Return Travel Mode')
	return_ticket = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Return ticket")
	return_preference = fields.Selection([('normal', 'Normal'), ('emergency', 'Emergency'), ('fast_track', 'Fast Track')], string='Return Booking Preference')
	return_from_location_id = fields.Many2one('location.master', string='Return From Location')
	return_to_location_id = fields.Many2one('location.master', string='Return To Location')
	returned_preffered_time = fields.Many2one('preferred.departure', string="Returned Preferred Time")
	return_date = fields.Date(readonly=True, string="Return Date")
	total_eligible_cost = fields.Float(string="Total Eligibility", compute="compute_total",track_visibility='onchange', digits=(16, 0))
	travel_advance = fields.Float(string="Advance",track_visibility='onchange', digits=(16, 0))
	additional_advance = fields.Float(string="Additional Advance",track_visibility='onchange', digits=(16, 0))
	total_advance = fields.Float(string="Total Advance", compute="compute_total",track_visibility='onchange', digits=(16, 0))
	balance_amount = fields.Float(string="Balance Amount", compute="compute_total",track_visibility='onchange', digits=(16, 0))
	attach_files = fields.Binary(string="Attach Files (Max~3MB)")
	store_attach_fname = fields.Char(string="Attach File Name")
	claim_status = fields.Selection([('verify', 'Verified'), ('pending', 'Pending')], default="pending", string="Claim status")
	justification = fields.Char('Justification')
	is_employee = fields.Boolean('Employee user', compute="compute_user")
	# is_accounts = fields.Boolean('Accounts user')
	app1_remarks = fields.Text('Approver 1 Remarks', readonly=True,track_visibility='onchange')
	hod_remarks = fields.Text('HOD Remarks', readonly=True,track_visibility='onchange')
	dir_remarks = fields.Text('Director Remarks', readonly=True,track_visibility='onchange')
	accounts_remarks = fields.Text('Accounts Remarks', readonly=True,track_visibility='onchange')
	acc_head_remarks = fields.Text('Accounts Head Remarks', readonly=True,track_visibility='onchange')
	user_id = fields.Many2one('res.users', string='User', compute="compute_user")
	conveyance_ids = fields.One2many('breakup.conveyance', 'claim_id', string='Conveyance')
	emp_date = fields.Datetime(readonly=True, string="Employee Date",track_visibility='onchange')
	app1_date = fields.Datetime(readonly=True, string="Approver 1 Date",track_visibility='onchange')
	hod_date = fields.Datetime(readonly=True, string="HOD Date",track_visibility='onchange')
	dir_date = fields.Datetime(readonly=True, string="Director Date",track_visibility='onchange')
	accounts_date = fields.Datetime(readonly=True, string="Accounts Date",track_visibility='onchange')
	acc_head_date = fields.Datetime(readonly=True, string="Accounts Head Date",track_visibility='onchange')
	is_justify = fields.Boolean('Is Justify')
	admin_emp_ids = fields.Many2many('hr.employee', string="Admin Employee", related="travel_admin_id.admin_emp_ids")
	accounts_head_emp_ids = fields.Many2many('hr.employee', string="Accounts Head Employee", related="travel_admin_id.accounts_head_emp_ids")
	accounts_emp_ids = fields.Many2many('hr.employee', string="Accounts Employee", related="travel_admin_id.accounts_emp_ids")
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
	hotel_ticket = fields.Binary(string="Hotel Bill (Max~3MB)")
	store_hotel_ticket = fields.Char(string="Hotel File Name")
	onward_ticket = fields.Binary(string="Onward Ticket (Max~3MB)", related="travel_admin_id.onward_ticket")
	store_onward_ticket = fields.Char(string="Onward File Name", related="travel_admin_id.store_fname")
	returned_ticket = fields.Binary(string="Return Ticket (Max~3MB)", related="travel_admin_id.returned_ticket")
	store_returned_ticket = fields.Char(string="Return File Name", related="travel_admin_id.store_return_fname")

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

	hr_reminder_approver1_ids = fields.Many2many('hr.employee', string='Noti1 Approver',
												 compute="compute_employee_approver1_id")
	hr_reminder_approver2_ids = fields.Many2many('hr.employee', string='Noti2 Approver',
												 compute="compute_employee_approver1_id")
	hr_reminder_hod_ids = fields.Many2many('hr.employee', string='Noti3 Approver',
										   compute="compute_employee_approver1_id")
	hr_reminder_director_ids = fields.Many2many('hr.employee', string='Noti4 Approver',
												compute="compute_employee_approver1_id")
	employee_ids = fields.Many2many('hr.employee', string='Noti5 Approver', compute="compute_employee_approver1_id")

	#added
	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('hr.travel.claim')
		rec = super(HrTravelClaim,self).create(vals)
		return rec

	@api.depends('user_id')
	def compute_user(self):
		for vals in self:
			current_employee = vals.env.uid
			vals.user_id = current_employee
			if self.employee_id.user_id.id == current_employee:
				self.is_employee = True

	# Multiple Mail for Accounts
	@api.multi
	def function_accounts(self):
		emails = []
		for users in self.accounts_head_emp_ids:
			emails.append(users.work_email)
		return emails
	@api.multi
	def function_accounts_verify(self):
		emails = []
		for users in self.accounts_emp_ids:
			emails.append(users.work_email)
		return emails

	@api.multi
	@api.onchange('food_eligibility', 'food_actual')
	def onchange_food(self):
		if self.food_eligibility:
			if self.food_eligibility < self.food_actual:
				raise ValidationError(_("Food-actual is not greater than Food-Eligibility."))

	@api.multi
	def submit_employee(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			self.emp_date = datetime.now()
			if self.local_conveyance == 0:
				raise ValidationError(_("You must give Local Conveyance."))
			# if self.accommodation != 'guest_house':
			# 	if self.actual_accommodation == 0:
			# 		raise ValidationError(_("You must give Accomodation-Actual."))
			self.state = 'approver1'
			template_id = self.env.ref('hr_travel.email_template_tc_approver1')                
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Claim',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
				'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],
				'hr_travel_claim_id': self.id
			})

	@api.multi
	def set_draft(self):
		self.state = 'draft'

	@api.multi
	def submit_approver1(self):
		var = self.function_accounts_verify()
		current_employee = self.env.uid
		is_app1 = self.employee_id.lone_manager_id.user_id.id
		if current_employee != is_app1:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app1:
			self.app1_date = datetime.now()
			# if self.is_justify == True:	
			self.state = 'hod'
			template_id = self.env.ref('hr_travel.email_template_tc_hod')                
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Claim Has Approved By Approver1',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
				'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
				'hr_travel_claim_id': self.id
			})

			# else:
			# 	self.state = 'accounts'
			# 	for vals in var:
			# 		template_id = self.env.ref('hr_travel.email_template_tc_accounts')
			# 		template_id.sudo().write({'email_to': vals})
			# 		template_id.sudo().send_mail(self.id, force_send=True)

	@api.multi
	def submit_hod(self):
		var = self.function_accounts_verify()
		current_employee = self.env.uid
		is_hod = self.employee_id.hod_id.user_id.id
		if current_employee != is_hod:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_hod:
			self.hod_date = datetime.now()
			if self.is_justify == True:	
				self.state = 'director'
				template_id = self.env.ref('hr_travel.email_template_tc_director')                
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Has Approved By HOD',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.hr_reminder_director_ids.ids)],
					'hr_travel_claim_id': self.id
				})
			else:
				self.state = 'accounts'
				for vals in var:
					template_id = self.env.ref('hr_travel.email_template_tc_accounts')
					template_id.sudo().write({'email_to': vals})
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Claim',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
						'approver_ids': [(6, 0, self.accounts_emp_ids.ids)],
						'hr_travel_claim_id': self.id
					})

	@api.multi
	def submit_director(self):
		var = self.function_accounts_verify()
		current_employee = self.env.uid
		is_dir = self.employee_id.parent_id.user_id.id
		if current_employee != is_dir:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_dir:
			self.dir_date = datetime.now()
			self.state = 'accounts'
			for vals in var:
				template_id = self.env.ref('hr_travel.email_template_tc_accounts')
				template_id.sudo().write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.accounts_emp_ids.ids)],
					'hr_travel_claim_id': self.id
				})


	@api.multi
	def submit_accounts(self):
		var = self.function_accounts()
		self.accounts_date = datetime.now()
		self.claim_status = 'verify'
		self.state = 'acc_head'
		for vals in var:
			template_id = self.env.ref('hr_travel.email_template_tc_accounts')
			template_id.sudo().write({'email_to': vals})
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Claim',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
				'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
				'hr_travel_claim_id': self.id
			})

	@api.multi
	def submit_acc_head(self):
		self.acc_head_date = datetime.now()
		self.state = 'approved'

	@api.multi
	def action_cancel(self):
		for reject in self:
			reject.state = 'cancelled'

	@api.multi
	def reject_app1(self):
		current_employee = self.env.uid
		is_app1 = self.employee_id.lone_manager_id.user_id.id
		if current_employee != is_app1:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app1:
			form_view = self.env.ref('hr_travel.form_claim_approver_remark_wizard')
			return {
				'name': "Approver Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'claim.request.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'travel_id': self.ids, 'is_reject': True
				}
			}

	@api.multi
	def reject_hod(self):
		current_employee = self.env.uid
		is_hod = self.employee_id.hod_id.user_id.id
		if current_employee != is_hod:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_hod:
			form_view = self.env.ref('hr_travel.form_travel_hod_remark_wizard')
			return {
				'name': "HOD Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.request.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'travel_id': self.ids, 'is_reject': True
				}
			}

	@api.multi
	def reject_director(self):
		current_employee = self.env.uid
		is_dir = self.employee_id.parent_id.user_id.id
		if current_employee != is_dir:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_dir:
			form_view = self.env.ref('hr_travel.form_travel_director_remark_wizard')
			return {
				'name': "Director Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.claim.director.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'travel_id': self.ids, 'is_reject': True
				}
			}

	@api.multi
	def reject_accounts(self):
		form_view = self.env.ref('hr_travel.form_claim_accounts_remark_wizard')
		return {
			'name': "Approver Remarks",
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': form_view.id,
			'res_model': 'travel.request.remark2',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
				'travel_id': self.ids, 'is_reject': True
			}
		}

	@api.multi
	def reject_acc_head(self):
		form_view = self.env.ref('hr_travel.form_claim_acc_head_remark_wizard')
		return {
			'name': "Accounts Head Remarks",
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': form_view.id,
			'res_model': 'travel.accounts.head.remark',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
				'travel_id': self.ids, 'is_reject': True
			}
		}

	@api.multi
	@api.depends('date_from', 'date_to')
	def compute_amount(self):
		for eligible in self:
			if eligible.date_to:
				accomp = 0
				food = 0
				delta = eligible.date_to - eligible.date_from
				days = delta.days+1
				remaining = days - 15
				var = 15
				policy = eligible.env['hr.travel.policy'].search([('employee_grade_id', '=', eligible.employee_id.employee_grade_id.id), ('days_range', '=', 'less_than_15days'),('city_category', '=', eligible.to_location_id.city_category)])
				if days <= 15:
					if policy.days_range == 'less_than_15days':
						if eligible.accommodation == 'self':
							eligible.acc_eligibility = (policy.amount * days)/2
							eligible.food_eligibility = (policy.amount_food * days)
						elif eligible.accommodation == 'hotel':
							eligible.acc_eligibility = policy.amount * days
							eligible.food_eligibility = policy.amount_food * days
						elif eligible.accommodation == 'guest_house':
							eligible.food_eligibility = policy.amount_food * days
				if days > 15:
					policy1 = eligible.env['hr.travel.policy'].search([('employee_grade_id', '=', eligible.employee_id.employee_grade_id.id), ('days_range', '=', 'more_than_15days'),('city_category', '=', eligible.to_location_id.city_category)])
					if var == 15:
						if policy.days_range == 'less_than_15days':
							accomp = policy.amount * 15
							food = policy.amount_food * 15
						if remaining > 0:
							if policy1.days_range == 'more_than_15days':
								if eligible.accommodation == 'self':
									eligible.acc_eligibility = ((policy1.amount * remaining)+(accomp)/2)
									eligible.food_eligibility = (policy1.amount_food * remaining)+(food)
								if eligible.accommodation == 'hotel':
									eligible.acc_eligibility = (policy1.amount * remaining)+(accomp)
									eligible.food_eligibility = (policy1.amount_food * remaining)+(food)
								if eligible.accommodation == 'guest_house':
									# self.acc_eligibility = (policy1.amount * remaining)+(accomp)
									eligible.food_eligibility = (policy1.amount_food * remaining)+(food)

	# Should not Complete the Travel Request Approver Should Block

	@api.model
	def _cron_notify_tc_approver(self):
		for vals in self.env['hr.travel.claim'].search([('state', 'in', ['approver1', 'hod', 'accounts', 'acc_head'])]):
			date = datetime.date(datetime.today())
			is_dir = vals.employee_id.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			if is_dir == False and vals.state == 'approver1':
				submit_date = vals.emp_date.date()
				notify = submit_date + relativedelta(days=2)
				if notify == date:
					template_id = self.env.ref('hr_travel.email_template_travel_claim_notified_blocked')
					template_id.sudo().send_mail(vals.id, force_send=True)
			elif is_dir == False and vals.state == 'hod':
				submit_hod = vals.app1_date.date()
				hod_notify = submit_hod + relativedelta(days=2)
				if hod_notify == date:
					template_id = self.env.ref('hr_travel.email_template_travel_claim_notified_blocked')
					template_id.sudo().send_mail(vals.id, force_send=True)
			elif is_dir == False and vals.state == 'accounts':
				var = vals.function_accounts_verify()
				submit_acc = vals.write_date.date()
				accounts_notify = submit_acc + relativedelta(days=2)
				if accounts_notify == date:
					template_id = self.env.ref('hr_travel.email_template_travel_claim_notified_blocked')
					template_id.sudo().send_mail(vals.id, force_send=True)
					for line in vals.accounts_emp_ids:
						for mail in var:
							template_id = self.env.ref('hr_travel.email_template_travel_claim_accounts_blocked_notify')
							template_id.sudo().write({'email_to': mail})
							template_id.sudo().send_mail(line.id, force_send=True)
		return True

	@api.model
	def _cron_block_tc_approver(self):
		for vals in self.env['hr.travel.claim'].sudo().search([('state', 'in', ['approver1', 'hod', 'accounts', 'acc_head'])]):
			date = datetime.date(datetime.today())
			leave_days = total = day_count = global_days_count = days_leave = leave_count = 0
			week_off_days_count = leave_delta_day = days_block = hol =  var = holiday_count = app_var = 0
			is_dir = vals.employee_id.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			app_date = vals.emp_date.date()
			if is_dir == False and vals.state == 'approver1':
				for leave in self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.lone_manager_id.id),('state','=','validate')]):
					if leave.request_date_to >= app_date and date >= leave.request_date_to:
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
				holiday_count = (date - app_date).days
				for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',vals.company_id.id),('work_location_id','=',vals.employee_id.lone_manager_id.location_work_id.id)]):
					app_var = holiday.date_from.date()
					if app_var >= app_date and app_var <= date:
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
				if app_date + relativedelta(days=(block_count)) <= date and vals.employee_id.lone_manager_id.user_id.is_blocked == False:
					vals.employee_id.lone_manager_id.user_id.is_blocked = True
					vals.employee_id.lone_manager_id.block_date = datetime.today().date()
					vals.employee_id.lone_manager_id.user_id.blocked_date = datetime.today().date()
					vals.employee_id.lone_manager_id.user_id.login_success = False
					# To create record in user account blocking menu - Starts
					blocking = self.env['blocked.details'].sudo().search([('blocked_date','=',date),('date','=',vals.date),('blocked_id','=',vals.employee_id.lone_manager_id.id)])
					if not blocking:
						block_hist = blocking.create({'blocked_id': vals.employee_id.lone_manager_id.id,
										'employee_id' : vals.employee_id.id,
										'reason' : 'Travel Claim is not approved',
										'blocked_date': date.today(),
										'date': vals.date,})

					acc = self.env['account.blocking']
					inv_line_obj = acc.sudo().create({'employee_id': vals.employee_id.lone_manager_id.id,
												'blocked_date': datetime.today().date(),
												'remark':'Travel Claim not approved till two days.'})
					# To create record in user account blocking menu - Ends
					# template_id = self.env.ref('hr_travel.email_template_travel_claim_blocked')
					# template_id.sudo().send_mail(vals.employee_id.lone_manager_id.id, force_send=True)
			elif is_dir == False and vals.state == 'hod':
				submit_hod = vals.app1_date.date()
				for leave in self.env['hr.leave'].sudo().search([('employee_id','=',vals.employee_id.hod_id.id),('state','=','validate')]):
					if leave.request_date_to >= submit_hod and date >= leave.request_date_to:
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
				holiday_count = (date - submit_hod).days
				for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',vals.company_id.id),('work_location_id','=',vals.employee_id.hod_id.location_work_id.id)]):
					app_var = holiday.date_from.date()
					if app_var >= submit_hod and app_var <= date:
						var = len(holiday)
						hol += var
				days_block = hol + 3 + leave_days
				start_weekoff = submit_hod
				end_weekoff = start_weekoff + relativedelta(days=(days_block))
				weekoff_delta_day = timedelta(days=1)
				week_off_days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
				st_dt = start_weekoff
				while st_dt <= end_weekoff:
					if st_dt.weekday() == week_off_days['Sunday']:
						week_off_days_count+=1
					st_dt += weekoff_delta_day
				block_count = week_off_days_count + days_block
				if submit_hod + relativedelta(days=(block_count)) <= date and vals.employee_id.hod_id.user_id.is_blocked == False:
					vals.employee_id.hod_id.user_id.is_blocked = True
					vals.employee_id.hod_id.user_id.blocked_date = date.today()
					vals.employee_id.hod_id.block_date = date.today()
					blocking_hod = self.env['blocked.details'].sudo().search([('blocked_date','=',date),('date','=',vals.date),('blocked_id','=',vals.employee_id.hod_id.id)])
					if not blocking_hod:
						block_hist = blocking_hod.create({'blocked_id': vals.employee_id.hod_id.id,
										'employee_id' : vals.employee_id.id,
										'reason' : 'Travel Claim is not approved',
										'blocked_date': date.today(),
										'date': vals.date,})
					acc = self.env['account.blocking']
					inv_line_obj = acc.sudo().create({'employee_id': vals.employee_id.hod_id.id,
												'blocked_date': datetime.today().date(),
												'remark':'Travel Claim not approved till two days.'})
					# template_id = self.env.ref('hr_travel.email_template_travel_claim_blocked')
					# template_id.sudo().send_mail(vals.employee_id.hod_id.id, force_send=True)
			elif is_dir == False and vals.state == 'accounts':
				var = vals.function_accounts_verify()
				submit_acc = vals.write_date.date()
				for leave in self.env['hr.leave'].sudo().search([('employee_id','=',vals.accounts_emp_ids.id),('state','=','validate')]):
					if leave.request_date_to >= submit_acc and date >= leave.request_date_to:
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
				holiday_count = (date - submit_acc).days
				for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',vals.company_id.id),('work_location_id','=',vals.accounts_emp_ids.location_work_id.id)]):
					app_var = holiday.date_from.date()
					if app_var >= submit_acc and app_var <= date:
						var = len(holiday)
						hol += var
				days_block = hol + 3 + leave_days
				start_weekoff = submit_acc
				end_weekoff = start_weekoff + relativedelta(days=(days_block))
				weekoff_delta_day = timedelta(days=1)
				week_off_days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
				st_dt = start_weekoff
				while st_dt <= end_weekoff:
					if st_dt.weekday() == week_off_days['Sunday']:
						week_off_days_count+=1
					st_dt += weekoff_delta_day
				block_count = week_off_days_count + days_block
				if submit_acc + relativedelta(days=(block_count)) <= date:
					for line in vals.accounts_emp_ids:
						if line.user_id.is_blocked == False:
							line.user_id.is_blocked = True
							line.user_id.blocked_date = date.today()
							line.block_date = date.today()
							blocking_acc = self.env['blocked.details'].sudo().search([('blocked_date','=',date),('date','=',vals.date),('blocked_id','=',line.id)])
							if not blocking_acc:
								block_hist = blocking_acc.sudo().create({'blocked_id': line.id,
												'employee_id' : vals.employee_id.id,
												'reason' : 'Travel Claim is not approved',
												'blocked_date': date.today(),
												'date': vals.date,})
							acc = self.env['account.blocking']
							inv_line_obj = acc.sudo().create({'employee_id': line.id,
														'blocked_date': datetime.today().date(),
														'remark':'Travel Claim not approved till two days.'})
						# for mail in var:
						# 	template_id = self.env.ref('hr_travel.email_template_travel_claim_accounts_blocked')
						# 	template_id.sudo().write({'email_to': mail})
						# 	template_id.sudo().send_mail(line.id, force_send=True)
			elif is_dir == False and vals.state == 'acc_head':
				var_head = vals.function_accounts()
				submit_head = vals.accounts_date.date()
				for leave in self.env['hr.leave'].sudo().search([('employee_id','=',vals.accounts_head_emp_ids.id),('state','=','validate')]):
					if leave.request_date_to >= submit_head and date >= leave.request_date_to:
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
				holiday_count = (date - submit_head).days
				for holiday in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',vals.company_id.id),('work_location_id','=',vals.accounts_head_emp_ids.location_work_id.id)]):
					app_var = holiday.date_from.date()
					if app_var >= submit_head and app_var <= date:
						var = len(holiday)
						hol += var
				days_block = hol + 3 + leave_days
				start_weekoff = submit_head
				end_weekoff = start_weekoff + relativedelta(days=(days_block))
				weekoff_delta_day = timedelta(days=1)
				week_off_days = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
				st_dt = start_weekoff
				while st_dt <= end_weekoff:
					if st_dt.weekday() == week_off_days['Sunday']:
						week_off_days_count+=1
					st_dt += weekoff_delta_day
				block_count = week_off_days_count + days_block
				if submit_head + relativedelta(days=(block_count)) <= date:
					for line_head in vals.accounts_head_emp_ids:
						if line_head.user_id.is_blocked == False:
							line_head.user_id.is_blocked = True
							line_head.user_id.blocked_date = date.today()
							line_head.block_date = date.today()
							blocking_acc = self.env['blocked.details'].sudo().search([('blocked_date','=',date),('date','=',vals.date),('blocked_id','=',line_head.id)])
							if not blocking_acc:
								block_hist = blocking_acc.sudo().create({'blocked_id': line_head.id,
												'employee_id' : vals.employee_id.id,
												'reason' : 'Travel Claim is not approved',
												'blocked_date': date.today(),
												'date': vals.date,})
							acc = self.env['account.blocking']
							inv_line_obj = acc.sudo().create({'employee_id': line_head.id,
														'blocked_date': datetime.today().date(),
														'remark':'Travel Claim not approved till two days.'})

		return True
	
class BreakupConveyance(models.Model):
	_name = 'breakup.conveyance'
	_description = 'Breakup Conveyance'

	name = fields.Char(string="Name")
	state = fields.Selection([('draft', 'Draft'),('approver1', 'Approver 1'),('hod', 'HOD'),
		('accounts', 'Accounts'),('acc_head', 'Accounts Head'), ('approved', 'Approved'),('rejected', 'Rejected'),('cancelled', 'Cancelled')],
							 string='Status', default='draft', related="claim_id.state")
	date = fields.Date(string="Date", required=True)
	claim_id = fields.Many2one('hr.travel.claim', string='Claim')
	from_location = fields.Char(string='From Location')
	to_location = fields.Char(string='To Location')
	mode_type_id = fields.Many2one('claim.mode', string='Mode Type')
	amount = fields.Float(string='Fare', digits=(16, 0))
	justification = fields.Char(string='Justification')
	attachments = fields.Binary(string='Attachments (Max~3MB)')
	store_attachments_fname = fields.Char(string='Attachments')
	
	@api.multi
	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			for date in self.claim_id:
				from_date = date.departure_date + relativedelta(days=(-1))
				to_date = date.date_to + relativedelta(days=(+1))
				if self.date < from_date or self.date > to_date:
					raise ValidationError(_("Date should between Departure Date and End Date.."))

class ClaimMode(models.Model):
	_name = 'claim.mode'
	_description = 'Claim Mode'
	_inherit = ['mail.thread']

	name = fields.Char(string="Name", required=True)
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name")
	updated_on = fields.Datetime("Updated On")

