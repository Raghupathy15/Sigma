# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

class HrTravelAdmin(models.Model):
	_name = 'hr.travel.admin'
	_description = 'Travel Request'
	_inherit = ['mail.thread']
	_order = 'id desc'

	def _get_employee_id(self):
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	# Check location
	@api.multi
	@api.onchange('to_location_id','from_location_id','return_ticket','date_from','return_date')
	def onchange_to_location_id(self):
		if self.return_date and self.date_from:
			self.no_of_days = ((self.return_date-self.date_from).days+1)
		if self.to_location_id:
			if self.from_location_id == self.to_location_id:
				raise ValidationError(_("From Location and To Location should be different !.."))
		if self.return_ticket == 'yes' or self.travel_type == 'round_trip':
			self.return_from_location_id = self.to_location_id
			self.return_to_location_id = self.from_location_id
		else:
			self.return_from_location_id = False
			self.return_to_location_id = False

	@api.multi
	@api.onchange('travel_extend', 'additional_advance', 'return_ticket')
	def onchange_extend(self):
		if self.travel_extend == 'yes':
			self.is_extend = True
		else:
			self.is_extend = False

		if self.additional_advance == 'yes':
			self.is_add_advance = True
		else:
			self.is_add_advance = False

		if self.return_ticket == 'yes':
			self.is_return_ticket = True
		elif self.return_ticket != 'yes':
			self.is_return_ticket = False
			self.is_return_trip = False
			# self.return_date = False
			# self.returned_preffered_time = False
			# self.return_travel_mode_id = False

	@api.multi
	@api.onchange('travel_advance')
	def onchange_travel_advance(self):
		for rec in self:
			if rec.travel_advance == 'no':
				rec.approved_advance = 0

	@api.multi
	@api.onchange('departure_date','date_from')
	def onchange_departure_date(self):
		for rec in self:
			if rec.departure_date and rec.date_from:
				if rec.departure_date > rec.date_from:
					raise ValidationError(_("Should select the Departure Date is less than From Date."))

	@api.multi
	@api.onchange('priority_type', 'return_preference')
	def onchange_priority_fasttrack(self):
		if self.state == 'draft':
			if self.priority_type == 'fast_track':
				raise ValidationError(_("You are not able to select Fast track in Priority"))
		elif self.state == 'travelling':
			if self.return_preference == 'fast_track':
				raise ValidationError(_("You are not able to select Fast track in Return Preference"))

	@api.multi
	@api.onchange('departure_date','priority_type')
	def onchange_priority(self):
		date = fields.Date.today()
		normal_date = date + relativedelta(days=2)
		if self.departure_date:
			if self.departure_date < date:
				raise ValidationError(_("Departure date Should not be less Today"))
			elif self.priority_type == 'normal':
				if self.departure_date:
					if self.departure_date < normal_date:
						raise ValidationError(_("Departure date Should be more than 2 days from Requested date"))

	@api.multi
	@api.onchange('date_from')
	def onchange_exist_request(self):
		for travel in self:
			travel_req = self.env['hr.travel.admin'].search([('date_from', '=', travel.date_from),('employee_id', '=', travel.employee_id.id),('state', '!=', 'cancelled')])
			for vals in travel_req:
				if travel.date_from:
					if vals.employee_id == travel.employee_id:
						raise ValidationError(_('Already Created a Travel Request for given Date'))

	@api.multi
	@api.onchange('date_from')
	def onchange_warning_request(self):
		for travel in self:
			travel_req = self.env['hr.travel.admin'].search([('employee_id', '=', travel.employee_id.id),('state', 'in', ['submit_approver1','submit_hod'])])
			for vals in travel_req:
				if travel.state == 'draft' and travel.date_from:
					if vals.is_cancel == True:
						raise ValidationError(_('Already Created a Travel Request for a Employee'))

	@api.onchange('travel_mode_id', 'priority_type', 'return_travel_mode_id')
	def onchange_oneway_mode_type(self):
		res = {}
		if self.state == 'draft' and self.priority_type == 'normal':
			res['domain'] = {'travel_mode_id': [('emp_grade_id','=',self.emp_grade.id)]}
		else:
			res['domain'] = {'travel_mode_id': []}
		
		return res

	@api.onchange('return_travel_mode_id', 'return_preference')
	def onchange_return_mode_type(self):
		res = {}
		if self.state == 'travelling' and self.return_preference == 'normal':
			res['domain'] = {'return_travel_mode_id': [('emp_grade_id','=',self.emp_grade.id)]}
		else:
			res['domain'] = {'return_travel_mode_id': []}
		return res

	@api.onchange('return_travel_mode_id', 'priority_type')
	def onchange_round_mode_type(self):
		res = {}
		if self.state == 'draft' and self.priority_type == 'normal':
			res['domain'] = {'return_travel_mode_id': [('emp_grade_id','=',self.emp_grade.id)]}
		else:
			res['domain'] = {'return_travel_mode_id': []}
		return res

	@api.depends('return_mode_type_id', 'is_change_mode')
	def _compute_return_get(self):
		res = {}
		if self.is_change_mode == 'yes':
			res['domain'] = {'return_mode_type_id': []}
		else:
			res['domain'] = {'return_mode_type_id': ['&',('travel_mode_id','=',self.return_travel_mode_id.id),('emp_grade_id','=',self.emp_grade.id)]}
		return res

	travel_request_id = fields.Many2one('hr.travel', string='Travel Request')
	name = fields.Char(default='New', copy=False, readonly=True, string="Name")
	date = fields.Date(readonly=True, default=fields.Date.context_today, string="Request Date")
	age = fields.Integer(string='Age', related="employee_id.age")
	aadhar_number = fields.Char(string='Aadhar Number', related="employee_id.aadhar_number")
	contact_no = fields.Char(string='Contact No', related="employee_id.contact_no")
	designation_id = fields.Many2one('employee.designation', string='Designation', related="employee_id.designation_id")
	employee_id = fields.Many2one('hr.employee', string='Employee', default=_get_employee_id, required=True)
	approver1_id = fields.Many2one('hr.employee', string='Approver 1', related="employee_id.lone_manager_id")
	approver2_id = fields.Many2one('hr.employee', string='Approver 2', related="employee_id.ltwo_manager_id")
	hod_id = fields.Many2one('hr.employee', string='HOD', related="employee_id.hod_id")
	director_id = fields.Many2one('hr.employee', string='Director', related="employee_id.parent_id")
	job_id = fields.Many2one('hr.job', string='Designation',related="employee_id.job_id")
	department_id = fields.Many2one('hr.department', string='Department',related="employee_id.department_id")
	priority_type = fields.Selection([('normal', 'Normal'), ('emergency', 'Emergency'), ('fast_track', ' ')], string='Priority')
	travel_type = fields.Selection([('one_way', 'One Way'), ('round_trip', 'Round Trip')],track_visibility='onchange')
	project_ref_id = fields.Many2one('project.project', string='Project Name')
	date_from = fields.Date(string="Perdiem Date",track_visibility='onchange')
	departure_date = fields.Date(string="Departure Date",track_visibility='onchange')
	date_to = fields.Date(string="End Date")
	preffered_departure_date = fields.Many2one('preferred.departure', string="Preffered Departure Time",track_visibility='onchange')
	no_of_days = fields.Integer(string="Number of Days",track_visibility='onchange')
	from_location_id = fields.Many2one('location.master', string='From Location')
	to_location_id = fields.Many2one('location.master', string='To Location')
	accommodation = fields.Selection([('guest_house', 'Guest House'), ('hotel', 'Hotel'), ('self', 'Self')], string='Accommodation')
	hotel_booking = fields.Selection([('self', 'Self'), ('admin', 'Travel Admin')], string='Hotel Booking by')
	# travel_mode = fields.Selection([('bus', 'Bus'), ('train', 'Train'), ('flight', 'Flight')], string='Travel Mode')
	# Field for travel mode by Raghu - Starts
	emp_grade = fields.Many2one('employee.grade', string="Employee Grade", related="employee_id.employee_grade_id")
	travel_mode_id = fields.Many2one('travel.mode.master','Travel Mode',track_visibility='onchange')	
	# Field for travel mode by Raghu - Ends

	mode_type_id = fields.Many2one('mode.type', 'Mode Type',domain="(['&',('travel_mode_id', '=', travel_mode_id),('emp_grade_id','=',emp_grade)])",track_visibility='onchange')
	# modify_travel_mode_id = fields.Many2one('travel.mode.master', 'Travel Mode')
	modify_mode_type_id = fields.Many2one('mode.type', 'Mode Type',domain="([('travel_mode_id', '=', travel_mode_id)])",track_visibility='onchange')
	travel_purpose = fields.Char(string="Travel Purpose")
	hotel_ticket = fields.Binary(string="Hotel Bill (Max~3MB)")
	store_hotel_fname = fields.Char(string="Hotel File Name")
	onward_ticket = fields.Binary(string="Onward Ticket (Max~3MB)")
	store_fname = fields.Char(string="File Name")
	store_return_fname = fields.Char(string="Return File Name")
	onward_ticket_cost = fields.Float('Onward Ticket Cost',track_visibility='onchange', digits=(16, 0))
	cancel_cost = fields.Float('Cancellation Cost',track_visibility='onchange', digits=(16, 0))
	hotel_cancel_cost = fields.Float('Hotel Cancel Cost',track_visibility='onchange', digits=(16, 0))
	booking_status = fields.Selection([('pending', 'Pending'), ('booked', 'Booked')], default="pending", string="Booking Status")
	travel_advance = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string='Travel Advance')
	approved_advance = fields.Float(string="Advance Amount",track_visibility='onchange', digits=(16, 0))
	additional_advance = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string="Additional Advance")
	travel_extend = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string="Travel Extend")
	days_extension = fields.Float(string="Days Extend",track_visibility='onchange', digits=(16, 0))
	is_extend = fields.Boolean('Is extend')
	is_add_advance = fields.Boolean('Is Advance')
	return_travel_mode_id = fields.Many2one('travel.mode.master','Return Travel Mode')
	return_mode_type_id = fields.Many2one('mode.type','Return Mode Type',domain="(['&',('travel_mode_id','=',return_travel_mode_id),('emp_grade_id','=',emp_grade)])",track_visibility='onchange')
	modify_return_mode_type_id = fields.Many2one('mode.type','Return Mode Type',domain="([('travel_mode_id','=',return_travel_mode_id)])",track_visibility='onchange')
	return_ticket = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string="Return ticket")
	return_preference = fields.Selection([('normal', 'Normal'), ('emergency', 'Emergency'), ('fast_track', 'Fast Track')], string='Return Booking Preference')
	return_from_location_id = fields.Many2one('location.master', string='Return From Location',track_visibility='onchange')
	return_to_location_id = fields.Many2one('location.master', string='Return To Location',track_visibility='onchange')
	returned_preffered_time = fields.Many2one('preferred.departure', string="Returned Preferred Time",track_visibility='onchange')
	is_mode = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Modify")
	extend_days = fields.Integer(string="Extend No of Days",track_visibility='onchange')
	additional_advance_amount = fields.Float(string="Additional Amount",track_visibility='onchange', digits=(16, 0))
	return_date = fields.Date(string="Return Date",track_visibility='onchange')
	preferred_area = fields.Char(string="Preferred Area",track_visibility='onchange')
	returned_ticket = fields.Binary(string="Return Ticket (Max~3MB)")
	state = fields.Selection([('draft', 'Draft'),('submit_approver1', 'Approver 1'), 
		('submit_approver2', 'Approver 2'),('submit_hod', 'HOD'),
		('submit_director', 'Director'),('submit_admin', 'Travel Admin'), ('submit_employee', 'Employee'),
		 ('submit_accounts', 'Accounts Head'),('travelling', 'Travelling'),('submit_claim', 'Submitted'), ('cancelled', 'Cancelled')],
							 string='Status', default='draft',track_visibility='onchange')
	is_employee = fields.Boolean('Employee user', compute="compute_user")
	is_admin = fields.Boolean('Admin Desk user', compute="compute_user")
	is_accounts = fields.Boolean('Accounts user', compute="compute_user")
	is_approve = fields.Boolean('Is Approve')
	is_cancel = fields.Boolean('Is Cancel')
	is_modify = fields.Boolean('Modify')
	is_return = fields.Boolean('Return')
	mode_type = fields.Selection([('bus', 'Bus'),('train', 'Train'),('flight', 'Flight')],string="Mode Type", related='travel_mode_id.mode_type')
	return_mode_type = fields.Selection([('bus', 'Bus'),('train', 'Train'),('flight', 'Flight')],string="Return Mode Type", related='return_travel_mode_id.mode_type')
	is_return_ticket = fields.Boolean('Return Ticket')
	is_return_trip = fields.Boolean('Return Trip')
	is_change_date = fields.Boolean('Change Date')
	is_modify_mode = fields.Boolean('Modify mode')
	is_change_mode = fields.Selection([('yes', 'Yes'),('no', 'No')], default="no", string='Change Mode')
	emp_remarks = fields.Text('Employee Remarks', readonly=True,track_visibility='onchange')
	app1_remarks = fields.Text('Approver 1 Remarks', readonly=True,track_visibility='onchange')
	app2_remarks = fields.Text('Approver 2 Remarks', readonly=True,track_visibility='onchange')
	hod_remarks = fields.Text('HOD Remarks', readonly=True,track_visibility='onchange')
	dir_remarks = fields.Text('Director Remarks', readonly=True,track_visibility='onchange')
	employee_date = fields.Datetime(readonly=True, string="Employee Date",track_visibility='onchange')
	app1_date = fields.Datetime(readonly=True, string="Approver 1 Date",track_visibility='onchange')
	app2_date = fields.Datetime(readonly=True, string="Approver 2 Date",track_visibility='onchange')
	hod_date = fields.Datetime(readonly=True, string="HOD Date",track_visibility='onchange')
	admin_date = fields.Datetime(readonly=True, string="Travel Admin Date",track_visibility='onchange')
	dir_date = fields.Datetime(readonly=True, string="Director Date",track_visibility='onchange')
	accounts_date = fields.Datetime(readonly=True, string="Accounts Date",track_visibility='onchange')
	complete_date = fields.Datetime(readonly=True, string="Complete Date",track_visibility='onchange')
	admin_remarks = fields.Text('Travel Admin Remarks', readonly=True ,track_visibility='onchange')
	modify_remarks = fields.Text('Travel Admin Modify Remarks', readonly=True ,track_visibility='onchange')
	user_id = fields.Many2one('res.users', string='User', compute="compute_user")
	booking_agent = fields.Char('Booking Agent / Travel' ,track_visibility='onchange')
	return_booking_agent = fields.Char('Return Booking Agent / Travel' ,track_visibility='onchange')
	hotel_cost = fields.Float('Hotel Cost',track_visibility='onchange', digits=(16, 0))
	return_ticket_cost = fields.Float('Return Ticket Cost',track_visibility='onchange', digits=(16, 0))
	city_category = fields.Selection([('A', 'A'), ('B+', 'B+'),('B', 'B'),
	 ('C', 'C')], string='City Category', related="to_location_id.city_category")
	cancelled = fields.Char('Cancelled', track_visibility='onchange')
	boarding_point = fields.Char('Boarding Point', track_visibility='onchange')
	return_boarding = fields.Char('Return Boarding Point' ,track_visibility='onchange')
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

	# Added New field/functions to edit adv amount - Raghu (START)
	edit_advance = fields.Boolean('Edit Advance')
	account_remarks = fields.Text('Accounts Remarks')
	admin_emp_ids = fields.Many2many('hr.employee', string="Admin Employee", compute="compute_admin_user")
	accounts_head_emp_ids = fields.Many2many('hr.employee', string="Accounts Head Employee", compute="compute_admin_user")
	accounts_emp_ids = fields.Many2many('hr.employee', string="Accounts Employee", compute="compute_admin_user")


	@api.depends('travel_type', 'priority_type', 'return_preference', 'return_ticket', 'is_change_mode')
	def compute_mode_type_access(self):
		for rec in self:
			if rec.travel_type == 'one_way' and rec.return_ticket != 'yes':
				if rec.priority_type == 'normal' and rec.is_change_mode == 'no':
					rec.mode_type_access = True
				elif rec.priority_type == 'normal' and rec.is_change_mode == 'yes':
					rec.mode_type_access = False
				elif rec.priority_type == 'emergency' or rec.priority_type == 'fast_track':
					rec.mode_type_access = False
			elif rec.travel_type == 'round_trip' and rec.return_ticket != 'yes':
				if rec.priority_type == 'normal' and rec.is_change_mode == 'no':
					rec.mode_type_access = True
				elif rec.priority_type == 'normal' and rec.is_change_mode == 'yes':
					rec.mode_type_access = False
				elif rec.priority_type == 'emergency' or rec.priority_type == 'fast_track':
					rec.mode_type_access = False
			elif rec.return_ticket == 'yes':
				if rec.return_preference == 'normal' and rec.is_change_mode == 'no':
					rec.mode_type_access = True
				elif rec.return_preference == 'normal' and rec.is_change_mode == 'yes':
					rec.mode_type_access = False
				elif rec.return_preference == 'emergency' or rec.return_preference == 'fast_track':
					rec.mode_type_access = False


	mode_type_access = fields.Boolean('Mode Type Access', compute='compute_mode_type_access')
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



	# Admin Desk User ID
	@api.multi
	@api.depends('employee_id')
	def compute_admin_user(self):
		for approve in self:
			admin_list=[]
			accounts_list=[]
			accounts_verify_list = []
			admin_desk_id = self.env['ir.model.data'].xmlid_to_res_id('hr_travel.group_kra_admin')
			accounts_id = self.env['ir.model.data'].xmlid_to_res_id('hr_travel.group_kra_accounts_head')
			accounts_verify_id = self.env['ir.model.data'].xmlid_to_res_id('hr_travel.group_kra_accounts')
			admin_mail = self.get_users_from_group(admin_desk_id)
			accounts_mail = self.get_users_from_group(accounts_id)
			accounts_verify_mail = self.get_users_from_group(accounts_verify_id)
			for vals in admin_mail:
				users = self.env['hr.employee'].search([('user_id', '=', vals),('company_id', '=', approve.company_id.id)])
				for emp in users:
					admin_list.append(emp.id)
					approve.admin_emp_ids = admin_list
			for acc_verify in accounts_verify_mail:
				users_verify = self.env['hr.employee'].sudo().search([('user_id', '=', acc_verify),('company_id', '=', approve.company_id.id)])
				for emp_verify in users_verify:
					accounts_verify_list.append(emp_verify.id)
					approve.accounts_emp_ids = accounts_verify_list
			for val_acc in accounts_mail:
				users_acc = self.env['hr.employee'].sudo().search([('user_id', '=', val_acc),('company_id', '=', approve.company_id.id)])
				for emp_acc in users_acc:
					accounts_list.append(emp_acc.id)
					approve.accounts_head_emp_ids = accounts_list
			

	#passing group id using self.env['ir.model.data'].xmlid_to_res_id('module.group_id')
	@api.multi
	def get_users_from_group(self,group_id):
		users_ids = []
		sql_query = """select uid from res_groups_users_rel where gid = %s"""               
		params = (group_id,)
		self.env.cr.execute(sql_query, params)
		results = self.env.cr.fetchall()
		for users_id in results:
			users_ids.append(users_id[0])
		return users_ids

	# Multiple Mail for Admin Desk
	@api.multi
	def function_admin(self):
		emails = []
		for users in self.admin_emp_ids:
			emails.append(users.work_email)
		return emails
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
	@api.onchange('approved_advance', 'additional_advance_amount',  'date_from', 'departure_date', 'preffered_departure_date', 'no_of_days', 'return_date')
	def onchange_edit_advance(self):
		if self.state == 'submit_accounts':
			self.edit_advance = True
		if self.state == 'submit_employee':
			self.is_change_date = True

	@api.multi
	@api.onchange('is_change_mode')
	def onchange_modify_mode(self):
		if self.state == 'submit_admin' and self.is_change_mode == 'yes':
			self.is_modify_mode = True
			self.is_modify = False
			self.mode_type_id = False
		elif self.state == 'submit_admin' and self.is_change_mode == 'no':
			self.is_modify_mode = False

	# Added New field/functions to edit adv amount - Raghu (END)

	#added
	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('hr.travel.admin')
		rec = super(HrTravelAdmin,self).create(vals)
		return rec

	@api.depends('user_id')
	def compute_user(self):
		for vals in self:
			current_employee = vals.env.uid
			vals.user_id = current_employee
			travel_admin = self.env.user.has_group('hr_travel.group_kra_admin')
			travel_accounts = self.env.user.has_group('hr_travel.group_kra_accounts_head')
			if travel_admin == True:
				vals.is_admin = True
			if travel_accounts == True:
				vals.is_accounts = True
			if self.employee_id.user_id.id == current_employee:
				self.is_employee = True

	@api.multi
	@api.constrains('date_from', 'departure_date', 'date_to', 'return_date')
	def _check_date_from(self):
		for complete in self:
			if complete.date_to:
				if complete.date_from > complete.date_to:
					raise ValidationError(_("Should select the End Date is more than From Date."))
				var = complete.date_from + relativedelta(days=(complete.no_of_days-1))
				if complete.date_to > var:
					raise ValidationError(_("End date should be less than no of days"))
		for date in self:
			if date.return_date and date.date_from:
				if date.date_from > date.return_date:
					raise ValidationError(_("Should select the Return Date is more than From Date."))
		
	@api.multi
	def reset_draft(self):
		for line in self:
			line.state = 'submit_admin'

	@api.multi
	def return_request(self):
		self.is_return_trip = True
		if self.is_return_trip == True and self.return_preference != 'fast_track':
			self.state = 'submit_approver1'
		elif self.is_return_trip == True and self.return_preference == 'fast_track':
			self.state = 'submit_hod'

	@api.multi
	def send_for_approver1(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			if self.no_of_days <= 0:
				raise UserError(_('You must give Number of days.'))
			self.employee_date = datetime.now()
			for approve in self:
				if approve.priority_type == 'fast_track' or approve.travel_mode_id.mode_type == 'flight':
					approve.is_approve = True
					# approve.is_return = True
					approve.state = 'submit_hod'
					template_id = self.env.ref('hr_travel.email_template_approval_fast_track')
					template_id.sudo().send_mail(approve.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				else:
					approve.is_approve = True
					approve.state = 'submit_approver1'
					template_id = self.env.ref('hr_travel.email_template_approval_normal_and_emergency')
					template_id.sudo().send_mail(approve.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],
						'hr_travel_admin_id': self.id
					})

	@api.multi
	def send_for_approver2(self):
		self.app1_date = datetime.now()
		for approve in self:
			if approve.priority_type == 'normal':
				approve.state = 'submit_approver2'
				template_id = self.env.ref('hr_travel.email_template_tr_approval')
				template_id.sudo().send_mail(approve.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Approved By Approver1',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.hr_reminder_approver2_ids.ids)],
					'hr_travel_admin_id': self.id
				})
			if approve.priority_type == 'emergency':
				approve.state = 'submit_hod'
				template_id = self.env.ref('hr_travel.email_template_hod_approval')
				template_id.sudo().send_mail(approve.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.id
				})

	@api.multi
	def submit_employee(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			self.employee_date = datetime.now()
			for approve in self:
				if approve.priority_type == 'fast_track':
					approve.state = 'submit_hod'
					template_id = self.env.ref('hr_travel.email_template_hod_approval')
					template_id.sudo().send_mail(approve.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				else:
					approve.state = 'submit_approver1'
					template_id = self.env.ref('hr_travel.email_template_approval_normal_and_emergency')
					template_id.sudo().send_mail(approve.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],
						'hr_travel_admin_id': self.id
					})

	@api.multi
	def submit_disagree_employee(self):
		var = self.function_admin()
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			self.employee_date = datetime.now()
			self.state = 'submit_admin'
			# for vals in var:
			template_id = self.env.ref('hr_travel.email_template_travel_admin')
			# template_id.sudo().write({'email_to': vals})
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.admin_emp_ids.ids)],
				'hr_travel_admin_id': self.id
			})

	@api.multi
	def action_approve1(self):
		current_employee = self.env.uid
		is_app1 = self.employee_id.lone_manager_id.user_id.id
		if current_employee != is_app1:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app1:
			self.app1_date = datetime.now()
			if self.is_return_trip == True:
				if self.return_preference == 'normal':
					self.state = 'submit_approver2'
					template_id = self.env.ref('hr_travel.email_template_tr_approval')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request Approved by Approver1',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver2_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				if self.return_preference == 'emergency':
					self.state = 'submit_hod'
					template_id = self.env.ref('hr_travel.email_template_approval_fast_track')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
						'hr_travel_admin_id': self.id
					})
			if self.is_extend == True:
				self.state = 'submit_hod'
				template_id = self.env.ref('hr_travel.email_template_for_hod_travel_extend')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.id
				})
			if self.is_add_advance == True:
				self.state = 'submit_hod'
				template_id = self.env.ref('hr_travel.email_template_for_additional_advance_hod')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Additional Advance Approved by Approver1',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.id
				})
			else:
				if self.priority_type == 'normal' and self.state != 'submit_hod':
					self.state = 'submit_approver2'
					template_id = self.env.ref('hr_travel.email_template_tr_approval')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request Approved by Approver1',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver2_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				if self.priority_type == 'emergency' and self.state != 'submit_hod':
					self.state = 'submit_hod'
					template_id = self.env.ref('hr_travel.email_template_approval_fast_track')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
						'hr_travel_admin_id': self.id
					})

	@api.multi
	def action_approve2(self):
		var = self.function_admin()
		current_employee = self.env.uid
		is_app2 = self.employee_id.ltwo_manager_id.user_id.id
		if current_employee != is_app2:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app2:
			self.app2_date = datetime.now()
			for approve in self:
				if self.return_travel_mode_id.mode_type == 'flight':
					self.state = 'submit_director'
					template_id = self.env.ref('hr_travel.email_template_director_approval')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_director_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				else:
					approve.state = 'submit_admin'
					# for vals in var:
					template_id = self.env.ref('hr_travel.email_template_travel_admin')
					# template_id.sudo().write({'email_to': vals})
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.admin_emp_ids.ids)],
						'hr_travel_admin_id': self.id
					})
	@api.multi
	def action_hod(self):
		var = self.function_admin()
		var_acc = self.function_accounts()
		current_employee = self.env.uid
		is_hod = self.employee_id.hod_id.user_id.id
		if current_employee != is_hod:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_hod:
			self.hod_date = datetime.now()
			if self.is_add_advance == True:
				self.travel_advance = 'yes'
				self.state = 'submit_accounts'
				for vals_acc in var_acc:
					template_id = self.env.ref('hr_travel.email_template_for_additional_advance_accounts')
					template_id.sudo().write({'email_to': vals_acc})
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Additional Advance Approved by HOD',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				# template_id = self.env.ref('hr_travel.email_template_for_additional_advance')
				# template_id.sudo().send_mail(self.id, force_send=True)

			elif self.is_extend == True:
				days = self.days_extension + self.no_of_days
				self.write({'no_of_days': days})
				self.state = 'travelling'
				self.travel_extend = 'no'
				self.is_extend = False
				self.days_extension = 0
				template_id = self.env.ref('hr_travel.email_template_employee_travelling')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Approved by HOD',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.employee_ids.ids)],
					'hr_travel_admin_id': self.id
				})
			else:
				if self.travel_mode_id.mode_type == 'flight' and self.is_return_trip == False and self.is_add_advance == False and self.is_extend == False:
					self.state = 'submit_director'
					template_id = self.env.ref('hr_travel.email_template_director_approval')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_director_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				elif self.return_travel_mode_id.mode_type == 'flight':
					self.state = 'submit_director'
					template_id = self.env.ref('hr_travel.email_template_director_approval')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_director_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				else:
					self.state = 'submit_admin'
					# for vals in var:
					template_id = self.env.ref('hr_travel.email_template_travel_admin')
					# template_id.sudo().write({'email_to': vals})
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Request',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.admin_emp_ids.ids)],
						'hr_travel_admin_id': self.id
					})
	@api.multi
	def return_admin(self):
		self.admin_date = datetime.now()
		form_view = self.env.ref('hr_travel.form_travel_admin_remark_wizard')
		return {
			'name': "Admin Remarks",
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': form_view.id,
			'res_model': 'travel.request.return',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
				'travel_id': self.ids, 'is_return': True
			}
		}
		for approve in self:
			approve.state = 'submit_employee'

	@api.multi
	def action_director(self):
		current_employee = self.env.uid
		is_dir = self.employee_id.parent_id.user_id.id
		if current_employee != is_dir:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_dir:
			var = self.function_admin()
			self.dir_date = datetime.now()
			for reject in self:
				reject.state = 'submit_admin'
				# for vals in var:
				template_id = self.env.ref('hr_travel.email_template_travel_admin')
				# template_id.write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.admin_emp_ids.ids)],
					'hr_travel_admin_id': self.id
				})

	@api.multi 
	def modify_admin(self):
		self.admin_date = datetime.now()
		form_view = self.env.ref('hr_travel.form_travel_modify_remark_wizard')
		return {
			'name': "Admin Remarks",
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': form_view.id,
			'res_model': 'travel.request.modify',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
				'travel_id': self.ids, 'is_modified': True
			}
		}

	@api.multi
	def send_for_accounts(self):
		var = self.function_accounts()
		self.admin_date = datetime.now()
		# if self.is_change_mode != 'yes':
		# 	if not self.mode_type_id:
		# 		raise ValidationError(_("You must give Mode Type"))
		# elif self.priority_type != 'normal':
		# 	if not self.modify_mode_type_id and self.is_return_trip == False:
		# 		raise ValidationError(_("You must give Mode Type"))
		if self.is_change_mode != 'yes':
			if not self.return_booking_agent and (self.travel_type == 'round_trip' or self.return_ticket == 'yes'):
				raise ValidationError(_("You must give Return Booking Agent"))
			if not self.mode_type_id and self.mode_type_access == True:
				raise ValidationError(_("You must give Mode Type"))
			elif not self.modify_mode_type_id and self.mode_type_access == False:
				raise ValidationError(_("You must give Mode Type"))
			if not self.return_mode_type_id and self.mode_type_access == True and (self.travel_type == 'round_trip' or self.return_ticket == 'yes'):
			# if not self.return_mode_type_id and (self.is_change_mode == 'yes' or self.return_preference == 'fast_track'):
				raise ValidationError(_("You must give Return Mode Type"))
			elif not self.modify_return_mode_type_id and self.mode_type_access == False and (self.travel_type == 'round_trip' or self.return_ticket == 'yes'):
				raise ValidationError(_("You must give Return Mode Type"))
		else:
			if not self.modify_return_mode_type_id and (self.is_change_mode == 'yes' or self.return_preference == 'fast_track'):
				raise ValidationError(_("You must give Return Mode Type"))
		if not self.booking_agent:
				raise ValidationError(_("You must give Booking Agent"))
		if self.hotel_booking == 'admin':
			if self.hotel_cost <= 0:
				raise ValidationError(_("You must give Hotel Cost"))
			else:
				self.state = 'travelling'
				template_id = self.env.ref('hr_travel.email_template_employee_travelling_admin')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request is Booked Successfully',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.employee_ids.ids)],
					'hr_travel_admin_id': self.id
				})
		if self.travel_advance == 'yes' and self.is_return_trip == False and self.is_extend == False and self.is_add_advance == False:
			self.booking_status = 'booked'
			self.state = 'submit_accounts'
			for vals in var:
				template_id = self.env.ref('hr_travel.email_template_tr_travel_accounts')
				template_id.write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
					'hr_travel_admin_id': self.id
				})
		elif self.travel_advance == 'yes'and self.is_return_trip == False and self.is_add_advance == True:
			self.booking_status = 'booked'
			self.state = 'submit_accounts'
			for vals in var:
				template_id = self.env.ref('hr_travel.email_template_tr_travel_accounts')
				template_id.write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
					'hr_travel_admin_id': self.id
				})
		elif self.travel_advance == 'no' and self.is_return_trip == False and self.is_add_advance == True:
			self.booking_status = 'booked'
			self.state = 'submit_accounts'
			for vals in var:
				template_id = self.env.ref('hr_travel.email_template_tr_travel_accounts')
				template_id.write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
					'hr_travel_admin_id': self.id
				})
		else:
			self.booking_status = 'booked'
			self.state = 'travelling'
			template_id = self.env.ref('hr_travel.email_template_employee_travelling_admin')
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request is Booked Successfully',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.employee_ids.ids)],
				'hr_travel_admin_id': self.id
			})

	@api.multi
	def action_accounts(self):
		self.accounts_date = datetime.now()
		if self.is_extend == True or self.is_add_advance == True:			
			self.sudo().write({'approved_advance': self.additional_advance_amount + self.approved_advance})
			self.state = 'travelling'
			self.travel_advance = 'yes'
			self.additional_advance = 'no'
			self.is_add_advance = False
			self.additional_advance_amount = 0
			days = self.days_extension + self.no_of_days
			self.sudo().write({'no_of_days': days})
			self.travel_extend = 'no'
			self.is_extend = False
			self.days_extension = 0
			template_id = self.env.ref('hr_travel.email_template_for_advance')
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request Advance Amount is Approved',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.employee_ids.ids)],
				'hr_travel_admin_id': self.id
			})

		else:
			self.state = 'travelling'
			if self.approved_advance > 0:
				template_id = self.env.ref('hr_travel.email_template_for_advance')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Advance Amount is Approved',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.employee_ids.ids)],
					'hr_travel_admin_id': self.id
				})

	@api.multi
	def request_advance(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if self.additional_advance_amount <= 0 and self.additional_advance == 'yes':
			raise UserError(_('You must give Additional Amount.'))
		if self.days_extension <= 0 and self.travel_extend == 'yes':
			raise UserError(_('Days Extend could not be null.'))
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		elif current_employee == is_employee:
			self.employee_date = datetime.now()
			for approve in self:
				approve.state = 'submit_approver1'
				if self.travel_extend == 'yes' and self.additional_advance != 'yes':
					template_id = self.env.ref('hr_travel.email_template_travel_extend')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Travel Extended',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],
						'hr_travel_admin_id': self.id
					})
				elif self.additional_advance == 'yes':
					template_id = self.env.ref('hr_travel.email_template_for_additional_advance')
					template_id.sudo().send_mail(self.id, force_send=True)
					hr_reminder = self.env['hr.reminder'].sudo().create({
						'name': 'Additional Advance Amount',
						'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
						'approver_ids': [(6, 0, self.hr_reminder_approver1_ids.ids)],
						'hr_travel_admin_id': self.id
					})

	@api.multi
	def action_claim(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			self.employee_date = datetime.now()
			if not self.date_to:
				raise ValidationError(_("You must give End Date"))
			self.complete_date = datetime.now()
			self.no_of_days = ((self.date_to-self.date_from).days+1)
			for val in self:
				travel = self.env['hr.travel.claim'].sudo().create({
				'employee_id': val.employee_id.id,
				'date_from': val.date_from,
				'date_to': val.date_to,
				'departure_date': val.departure_date,
				'preffered_departure_date': val.preffered_departure_date.id,
				'no_of_days': val.no_of_days,
				'project_ref_id': val.project_ref_id.id,
				'from_location_id': val.from_location_id.id,
				'to_location_id': val.to_location_id.id,
				'onward_ticket_cost': val.onward_ticket_cost,
				'travel_purpose': val.travel_purpose,
				'travel_advance': val.approved_advance,
				'approved_advance': val.approved_advance,
				'extend_days': val.extend_days,
				'accommodation': val.accommodation,
				'hotel_booking': val.hotel_booking,
				'additional_advance': val.additional_advance_amount,
				'travel_type': val.travel_type,
				'return_travel_mode_id': val.return_travel_mode_id.id,
				'return_ticket': val.return_ticket,
				'return_preference': val.return_preference,
				'return_from_location_id': val.return_from_location_id.id,
				'return_to_location_id': val.return_to_location_id.id,
				'returned_preffered_time': val.returned_preffered_time.id,
				'return_date': val.return_date,
				'hotel_ticket': val.hotel_ticket,
				'store_hotel_ticket': val.store_hotel_fname,
				'travel_request_id': val.travel_request_id.id,
				'travel_admin_id': val.id,
				})
			self.state = 'submit_claim'

	@api.multi
	def action_cancel(self):
		current_employee = self.env.uid
		is_employee = self.employee_id.user_id.id
		if current_employee != is_employee:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_employee:
			self.emp_date = datetime.now()
			if self.is_approve == True:
				form_view = self.env.ref('hr_travel.form_travel_employee_remark_wizard')
				return {
					'name': "Employee Remarks",
					'view_mode': 'form',
					'view_type': 'form',
					'view_id': form_view.id,
					'res_model': 'employee.cancel.remark',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'context': {
						'travel_id': self.ids, 'is_reject': True
					}
				}
				# self.is_cancel = True
				# self.state = 'submit_approver1'
		else:
			self.state = 'cancelled'

	@api.multi
	def cancelled_approve(self):
		current_employee = self.env.uid
		is_app1 = self.employee_id.lone_manager_id.user_id.id
		if current_employee != is_app1:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app1:
			if self.booking_status == 'booked':
				self.state = 'submit_hod'
				template_id = self.env.ref('hr_travel.email_template_hod_tr_cancel')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Cancelled',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.id
				})
			else:
				self.state = 'cancelled'

	@api.multi
	def cancelled_hod(self):
		var = self.function_admin()
		current_employee = self.env.uid
		is_hod = self.employee_id.hod_id.user_id.id
		if current_employee != is_hod:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_hod:
			self.state = 'submit_admin'
			# for vals in var:
			template_id = self.env.ref('hr_travel.email_template_travel_admin')
			# template_id.write({'email_to': vals})
			template_id.sudo().send_mail(self.id, force_send=True)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.admin_emp_ids.ids)],
				'hr_travel_admin_id': self.id
			})


	@api.multi
	def cancelled_admin(self):
		var = self.function_accounts()
		if self.cancel_cost <= 0:
			raise ValidationError(_('You must give Cancellation Cost.'))
		if self.approved_advance >= 0:
			self.state = 'submit_accounts'
			for vals in var:
				template_id = self.env.ref('hr_travel.email_template_tr_travel_accounts')
				template_id.sudo().write({'email_to': vals})
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.accounts_head_emp_ids.ids)],
					'hr_travel_admin_id': self.id
				})
		else:
			self.state = 'cancelled'

	@api.multi
	def approve_cancel_accounts(self):
		self.state = 'cancelled'

	@api.multi
	def reject_travel(self):
		current_employee = self.env.uid
		is_app1 = self.employee_id.lone_manager_id.user_id.id
		if current_employee != is_app1:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app1:
			self.app1_date = datetime.now()
			form_view = self.env.ref('hr_travel.form_travel_admin_approver1_remark_wizard')
			return {
				'name': "Approver Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.admin.app1.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'travel_id': self.ids, 'is_reject': True
				}
			}

	@api.multi
	def reject_app2(self):
		current_employee = self.env.uid
		is_app2 = self.employee_id.ltwo_manager_id.user_id.id
		if current_employee != is_app2:
			raise UserError(_('You are not a authorized user to perform actions in this document.'))
		if current_employee == is_app2:
			self.app2_date = datetime.now()
			form_view = self.env.ref('hr_travel.form_travel_admin_approver2_remark_wizard')
			return {
				'name': "Approver Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.admin.app2.remark',
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
			self.dir_date = datetime.now()
			form_view = self.env.ref('hr_travel.form_travel_director_remark_wizard')
			return {
				'name': "Director Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.director.remarks',
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
			self.hod_date = datetime.now()
			form_view = self.env.ref('hr_travel.form_travel_admin_hod_remark_wizard')
			return {
				'name': "HOD Remarks",
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': form_view.id,
				'res_model': 'travel.admin.hod.remark',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'travel_id': self.ids, 'is_reject': True
				}
			}

	# Should not Complete the Travel Request End User Should Block

	@api.model
	def _cron_block_tr_user(self):
		for vals in self.env['hr.travel.admin'].search([('state', '=', 'travelling')]):
			date = datetime.date(datetime.today())
			# notify = vals.date_from + relativedelta(days=(self.no_of_days+4))
			notify = vals.date_from + relativedelta(days=(self.no_of_days+5))
			block = vals.date_from - relativedelta(days=(self.no_of_days))
			if notify == date:
				template_id = self.env.ref('hr_travel.email_template_travel_request_notify_blocked')                
				template_id.sudo().send_mail(vals.id, force_send=True)
			if block == date:
				vals.employee_id.user_id.is_blocked = True
				template_id = self.env.ref('hr_travel.email_template_travel_request_blocked')                
				template_id.sudo().send_mail(vals.id, force_send=True)
		return True

	# if hod not approved in 60 minutes mail trigger to L2

	# Need to add library from dateutil.relativedelta import relativedelta

	@api.multi
	def _cron_change_state(self):
		rec = self.env['hr.travel.admin'].search([('state', '=', 'submit_hod'),('priority_type', '=', 'fast_track')])
		for record in rec:
			current_time = fields.datetime.now()
			write_date = record.write_date + relativedelta(hours=1)
			if write_date < current_time and record.booking_status == 'pending':
				record.state = 'submit_approver2'
				template_id = self.env.ref('hr_travel.email_template_hod_not_approved')
				template_id.sudo().send_mail(record.id, force_send=True)
		return True


class HrTravelPolicy(models.Model):
	_name = 'hr.travel.policy'
	_inherit = ['mail.thread']

	name = fields.Char(string="Name")
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
	employee_grade_id = fields.Many2one('employee.grade', 'Grade', track_visibility='onchange')
	days_range = fields.Selection([('less_than_15days', 'Less than 15Days'),('more_than_15days', 'More than 15Days')], track_visibility='onchange')
	allowance_type = fields.Selection([('lodging_allowance', 'Lodging'), ('food_allowance', 'Food')], track_visibility='onchange')
	city_category = fields.Selection([('A', 'A'), ('B+', 'B+'),('B', 'B'),
	 ('C', 'C')], string='City Category', track_visibility='onchange')
	amount = fields.Float(string="Lodging Amount", required=True, digits=(16, 0), track_visibility='onchange')
	amount_food = fields.Float(string="Food Amount", required=True, digits=(16, 0), track_visibility='onchange')
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name", track_visibility='onchange')
	updated_on = fields.Datetime("Updated On", track_visibility='onchange')

	@api.multi
	@api.onchange('employee_grade_id','allowance_type','city_category','amount','amount_food')
	def onchange_updated_on(self):
		for record in self:
			record.updated_on = datetime.today()

class LocationMaster(models.Model):
	_name = 'location.master'
	_inherit = ['mail.thread']

	name = fields.Char(string="Name", required=True, track_visibility='onchange')
	city_category = fields.Selection([('A', 'A'), ('B+', 'B+'),('B', 'B'),
	 ('C', 'C')], string='City Category', track_visibility='onchange')
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name", track_visibility='onchange')
	updated_on = fields.Datetime("Updated On", track_visibility='onchange')
	active=fields.Boolean('Active',default=True)

	@api.multi
	@api.onchange('name', 'city_category')
	def onchange_updated_on(self):
		for record in self:
			record.updated_on = datetime.today()

class ModeType(models.Model):
	_name = 'mode.type'
	_inherit = ['mail.thread']

	name = fields.Char(string="Name", required=True, track_visibility='onchange')
	travel_mode_id = fields.Many2one('travel.mode.master','Mode Type', track_visibility='onchange')
	emp_grade_id = fields.Many2many('employee.grade', string="Employee Grade",required=True, track_visibility='onchange')
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name", track_visibility='onchange')
	updated_on = fields.Datetime("Updated On", track_visibility='onchange')

	@api.multi
	@api.onchange('name', 'travel_mode_id', 'emp_grade_id')
	def onchange_updated_on(self):
		for record in self:
			record.updated_on = datetime.today()


class PreferredDeparture(models.Model):
	_name = 'preferred.departure'
	_inherit = ['mail.thread']

	name = fields.Char(string="Name", required=True, track_visibility='onchange')
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name", track_visibility='onchange')
	updated_on = fields.Datetime("Updated On", track_visibility='onchange')

	@api.multi
	@api.onchange('name')
	def onchange_updated_on(self):
		for record in self:
			record.updated_on = datetime.today()

# Travel mode master starts - Raghu
class TravelModeMaster(models.Model):
	_name = 'travel.mode.master'
	_inherit = ['mail.thread']

	name = fields.Char(string="Travel Mode")
	mode_type = fields.Selection([('bus', 'Bus'),('train', 'Train'),('flight', 'Flight')],string="Mode Type", track_visibility='onchange')
	emp_grade_id = fields.Many2many('employee.grade', string="Employee Grade",required=True)
	created_by = fields.Char("Created By",related="create_uid.name")
	created_on = fields.Datetime("Created On",default=datetime.now())
	updated_by = fields.Char("Updated By",related="write_uid.name")
	updated_on = fields.Datetime("Updated On")

	@api.multi
	@api.onchange('name','emp_grade_id')
	def onchange_updated_on(self):
		for record in self:
			record.updated_on = datetime.now()

# Travel mode master ends - Raghu

class ResUsersInherit(models.Model):
	_inherit = 'res.users'

	@api.one
	def _compute_employee_id(self):
		for vals in self:
			employee_data = self.env['hr.employee'].sudo().search([('user_id', '=', vals.id)])
			for data in employee_data:
				vals.employee_id = data.id
				vals.employee_code = data.employee_id
	employee_id = fields.Many2one('hr.employee', string='Employee', compute='_compute_employee_id', store=True)
	employee_code = fields.Char(string='Employee Code', compute='_compute_employee_id', store=True)

	@api.multi
	def name_get(self):
		result = []
		for line in self:
			name = str(line.employee_code) + ' - ' + line.name
			result.append((line.id, name))
		return result
