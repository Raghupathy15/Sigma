# -*- coding: utf-8 -*-
import time
from datetime import timedelta
from datetime import datetime
from datetime import date
from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

class EmployeeEducationLine(models.Model):
	_name = 'employee.education.line'

	employee_id = fields.Many2one('hr.employee',string='Employee ID')
	istitute_name = fields.Char("Institute Name")
	qualification = fields.Char("Qualification")
	pass_out_year = fields.Char("Pass Out Year")
	qualification_documents = fields.Binary("Qualification Documents (Max~3MB)")


class company_property(models.Model):
	_name = 'company.property'

	name = fields.Char('Name')

class EmployeeGrade(models.Model):
	_name = 'employee.grade'
	_inherit = ['mail.thread']
	_description = 'Employee Grade'
	_order = 'name'

	name = fields.Char("Name",track_visibility='onchange')
	desc = fields.Char("Description")
	created_by = fields.Char("Created By",related="create_uid.name")
	updated_by = fields.Char("Updated By",related="write_uid.name")


class HrDepartment(models.Model):
	_inherit = 'hr.department'

	desc = fields.Char("Description")
	created_by = fields.Char("Created By",related="create_uid.name")
	updated_by = fields.Char("Updated By",related="write_uid.name")


class WorkLocation(models.Model):
	_name = 'work.location'
	_inherit = ['mail.thread']
	_description = 'Work Location'

	name = fields.Char("Name",track_visibility='onchange')
	desc = fields.Char("Description")
	created_by = fields.Char("Created By",related="create_uid.name")
	updated_by = fields.Char("Updated By",related="write_uid.name")


class EmployeeDesignation(models.Model):
	_name = 'employee.designation'
	_inherit = ['mail.thread']
	_description = 'Employee Designation'

	name = fields.Char("Name",track_visibility='onchange')
	desc = fields.Char("Description")
	created_by = fields.Char("Created By",related="create_uid.name")
	updated_by = fields.Char("Updated By",related="write_uid.name")
	active=fields.Boolean('Active',default=True)

class blocked_details(models.Model):
		_name = "blocked.details"
		_order = "id desc"

		blocked_id = fields.Many2one('hr.employee',string='Blocked')
		employee_id = fields.Many2one('hr.employee',string='Employee')
		# name = fields.Integer('Total Unblocked',readonly=True)
		date = fields.Date('Date',readonly=True)
		reason = fields.Text('Blocked Remarks',readonly=True)
		user_id = fields.Many2one('res.users','Blocked By',readonly=True)
		timesheet_id = fields.Many2one('account.analytic.line','Timesheet',readonly=True)
		blocked_date = fields.Date('Blocked Date',readonly=True)

class unblocked_details(models.Model):
		_name = "unblocked.details"
		_order = "id desc"

		unblocked_id = fields.Many2one('hr.employee',string='Unblocked')
		name = fields.Integer('Total Unblocked',readonly=True)
		date = fields.Datetime('Date',readonly=True)
		reason = fields.Text('Unblocked Remarks',readonly=True)
		user_id = fields.Many2one('res.users','Unblocked By',readonly=True)


class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	@api.multi
	@api.onchange('attendance_type')
	def onchange_inactive(self):
		for vals in self:
			if vals.attendance_type == 'rfid':
				vals.device_id = False

	@api.depends('birthday')
	def compute_calculateAge(self):
		for vals in self:
			if vals.birthday:
				today = date.today()
				vals.age = int((today - vals.birthday).days/365.25)

	device_id = fields.Char(string='Device ID',track_visibility='onchange')
	payroll = fields.Selection([('yes','Yes'),('no','No')], default="yes", string='Payroll',track_visibility='onchange')
	parent_id = fields.Many2one('hr.employee', 'Director', track_visibility='onchange')
	employee_id = fields.Char(string='Employee ID', required=False,track_visibility='onchange')
	employee_grade_id = fields.Many2one('employee.grade',string='Grade', required=False,track_visibility='onchange')
	timesheet = fields.Selection([('yes','Yes'),('no','No')],default='yes',string='Timesheet',track_visibility='onchange')
	block_date = fields.Date(string='Block Date')
	appraisal_date = fields.Date(string='Appraisal Date', required=False,track_visibility='onchange')
	joining_date = fields.Date(string='DOJ',default=datetime.now().strftime('%Y-%m-%d'),track_visibility='onchange')
	age = fields.Integer(string='Age', compute="compute_calculateAge", track_visibility='onchange')
	employment_status = fields.Selection([
		('probation', 'Probation'),
		('confirmed', 'Confirmed')
	], string='Employment Status', default="probation",required=False,track_visibility='onchange')
	id_proofs = fields.Many2many('ir.attachment', 'emp_eci_ir_attachments_rel',
								 'employee_id', 'attachment_id', string='ID Proofs', required=False,track_visibility='onchange')
	work_document_ids = fields.Many2many('ir.attachment', 'work_document_emp_ir_attachments_rel',
								'work_document_employee_id', 'work_document_attachment_id', string='Employee Work Documents', required=False,track_visibility='onchange')
	provisional_certificate_ids = fields.Many2many('ir.attachment', 'provisional_emp_ir_attachments_rel',
								'provisional_employee_id', 'provisional_attachment_id', string='Provisional Certificates', required=False,track_visibility='onchange')
	designation_id = fields.Many2one('employee.designation','Designation',track_visibility='onchange')
	lone_manager_id = fields.Many2one('hr.employee', 'Approver 1', required=False,track_visibility='onchange')
	ltwo_manager_id = fields.Many2one('hr.employee', 'Approver 2', required=False,track_visibility='onchange')
	hod_id = fields.Many2one('hr.employee', 'HOD', required=False,track_visibility='onchange')
	director_id = fields.Many2one('hr.employee', 'Director', required=False,track_visibility='onchange')
	exit_date = fields.Date(string='Last Working Date',track_visibility='onchange')
	wedding_anniversary_date = fields.Date(string='Wedding Anniversary Date',track_visibility='onchange')
	resigned = fields.Selection([
		('resign_yes', 'Yes'),
		('resign_no', 'No')
	], string='Resigned',track_visibility='onchange')
	employee_email = fields.Char(string='Personal Email ID',track_visibility='onchange')
	qualification = fields.Char(string='Qualification', required=False,track_visibility='onchange')
	previous_employer_detail = fields.Selection([
		('applicable', 'Applicable'),
		('not_applicable', 'Not Applicable')
	], string='Previous Employer Details', required=False,track_visibility='onchange')
	total_work_exp = fields.Selection([
		('applicable', 'Applicable'),
		('not_applicable', 'Not Applicable')
	], string='Total Number of Working Experience before Joining', required=False,track_visibility='onchange')
	upload_cv = fields.Binary('Upload Employee CV (Max~3MB)', attachment=True, required=False,track_visibility='onchange')
	filename = fields.Char('Filename',track_visibility='onchange')
	account_no = fields.Char('Bank Account',track_visibility='onchange')
	bank_name = fields.Char('Bank Name',track_visibility='onchange')
	ifsc_code = fields.Char('Bank IFSC Code',track_visibility='onchange')
	branch_name = fields.Char('Branch Name',track_visibility='onchange')
	pf_number = fields.Char(string='PF No', required=False,track_visibility='onchange')
	uan_number = fields.Char(string='UAN No', required=False,track_visibility='onchange')
	esic_number = fields.Char(string='ESIC No', required=False,track_visibility='onchange')
	blood_group = fields.Selection([('o_positive','O+'),('o_negative','O-'),('a_positive','A+'),
									('a_negative','A-'),('b_positive','B+'),('b_negative','B-'),
									('ab_positive','AB+'),('ab_negative','AB-')],string='Blood Group', required=False,track_visibility='onchange')
	religion = fields.Char(string='Religion', required=False,track_visibility='onchange')
	emergency_no = fields.Char('Emergency Contact',track_visibility='onchange')
	experience = fields.Selection([('fresher','Fresher'),('experienced','Experienced')],string="Experience",track_visibility='onchange')
	years_experience = fields.Integer('Years of Experience',track_visibility='onchange')
	experience_docs = fields.Binary('Upload Experience Documents (Max~3MB)',track_visibility='onchange')
	experience_docs_name = fields.Char(string='Attachments')
	attendance_type = fields.Selection([
		('rfid', 'RFID'),
		('mobile_app', 'Mobile App'),
		('geo_fence', 'Geo Fence')
	], string='Attendance Type', required=False,track_visibility='onchange')
	
	resignation_date = fields.Date(string='Resignation Date',track_visibility='onchange')
	location = fields.Char(string='Location', required=False,track_visibility='onchange')
	contact_no = fields.Char(string='Contact No', required=True,track_visibility='onchange')
	pan_number = fields.Char(string='PAN Number', required=False,track_visibility='onchange')
	aadhar_number = fields.Char(string='Aadhar Number', required=False,track_visibility='onchange')
	driving_license = fields.Char(string='Driving License', required=False,track_visibility='onchange')
	passport = fields.Char(string='Passport', required=False,track_visibility='onchange')
	doc_pan_number = fields.Binary('Upload Pan Card (Max~3MB)',track_visibility='onchange')
	doc_pan_name = fields.Char(string='Attachments')
	doc_aadhar_number = fields.Binary('Upload Aadhar Card (Max~3MB)',track_visibility='onchange')
	doc_aadhar_name = fields.Char(string='Attachments')
	doc_driving_license = fields.Binary('Upload Driving License (Max~3MB)',track_visibility='onchange')
	doc_driving_name = fields.Char(string='Attachments')
	doc_passport = fields.Binary('Upload Passport (Max~3MB)',track_visibility='onchange')
	doc_passport_name = fields.Char(string='Attachments')
	employee_education_line = fields.One2many('employee.education.line','employee_id',string='Education Details',track_visibility='onchange')
	company_property = fields.Many2many('company.property', string="Company Property",track_visibility='onchange')
	state = fields.Selection([('draft','Draft'),('to_approve','To Approve'),('approved','Approved')],string="Status",default="draft",track_visibility='onchange')
	is_hr = fields.Boolean("Is HR", compute='_compute_is_hr',track_visibility='onchange')
	is_employee = fields.Boolean("Is Employee", compute='_compute_is_hr',track_visibility='onchange')
	location_work_id = fields.Many2one('work.location',string="Work Location",track_visibility='onchange')
	manager_remark_unblock = fields.Char(string='Manager Remarks for Unblock',track_visibility='onchange',invisible=False)
	hr_remark_unblock = fields.Char(string='HR Remarks for Unblock',track_visibility='onchange',invisible=False)
	is_blocked = fields.Boolean(string='Is Blocked', related='user_id.is_blocked',track_visibility='onchange')
	emp_confirmation_date = fields.Date(string='Employee Confirmation Date',track_visibility='onchange')
	probation_eval_date = fields.Date(string='Probation Evaluation Date', required=False, track_visibility='onchange',compute='_compute_confirmation')
	probation_eval_date1 = fields.Date(string='Probation Evaluation Date', required=False,track_visibility='onchange')
	disclaimer_family = fields.Boolean(string="DISCLAIMER:- I certify that the information contained in this application and in any attachments to this application is correct to the best of my knowledge, and I understand that falsifications and/or omissions in any detail are grounds for disqualification from consideration for employment or, if hired, for dismissal from employment. I further understand that, if hired, my employment and compensation can be terminated, with or without cause, and with or without notice at any time, at the option of either myself or SigmaAVIT.",default=False,track_visibility='onchange')
	disclaimer_experience = fields.Boolean(string="DISCLAIMER:- I certify that the information contained in this application and in any attachments to this application is correct to the best of my knowledge, and I understand that falsifications and/or omissions in any detail are grounds for disqualification from consideration for employment or, if hired, for dismissal from employment. I further understand that, if hired, my employment and compensation can be terminated, with or without cause, and with or without notice at any time, at the option of either myself or SigmaAVIT.",default=False,track_visibility='onchange')
	disclaimer_id_details = fields.Boolean(string="DISCLAIMER:- I certify that the information contained in this application and in any attachments to this application is correct to the best of my knowledge, and I understand that falsifications and/or omissions in any detail are grounds for disqualification from consideration for employment or, if hired, for dismissal from employment. I further understand that, if hired, my employment and compensation can be terminated, with or without cause, and with or without notice at any time, at the option of either myself or SigmaAVIT.",default=False,track_visibility='onchange')
	blocked_ids = fields.One2many('blocked.details','blocked_id',string='blocked History')
	unblocked_ids = fields.One2many('unblocked.details','unblocked_id',string='Unblocked History')
	android_notification_token = fields.Char(string='Android Notification Token', invisible=True)
	self_declare_edit = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
										 string="Access to Create Self Declaration")
	self_declare_document = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
											 string="Access to Upload Document in Self Declaration")

	@api.multi
	@api.constrains('father_name','father_dob','mother_name','mother_dob','current_address','permanent_address','marital_status','aadhar_number',
		'birthday','blood_group','contact_no','country_id','driving_license','employee_grade_id','exceptions','gender',
		'joining_date','pan_number','passport_id','religion','years_experience')
	def _check_disclaimer(self):
		for line in self:
			if line.father_name and line.disclaimer_family == False:
				raise ValidationError(_("1Please check the desclaimer to ensure that the details you have entered are true"))
			if line.father_dob and line.disclaimer_family == False:
				raise ValidationError(_("2Please check the desclaimer to ensure that the details you have entered are true"))
			if line.mother_name and line.disclaimer_family == False:
				raise ValidationError(_("3Please check the desclaimer to ensure that the details you have entered are true"))
			if line.mother_dob and line.disclaimer_family == False:
				raise ValidationError(_("4Please check the desclaimer to ensure that the details you have entered are true"))
			if line.current_address and line.disclaimer_family == False:
				raise ValidationError(_("5Please check the desclaimer to ensure that the details you have entered are true"))
			if line.permanent_address and line.disclaimer_family == False:
				raise ValidationError(_("6Please check the desclaimer to ensure that the details you have entered are true"))
			if line.marital_status and line.disclaimer_family == False:
				raise ValidationError(_("7Please check the desclaimer to ensure that the details you have entered are true"))
			if line.aadhar_number and line.disclaimer_id_details == False:
				raise ValidationError(_("8Please check the desclaimer to ensure that the details you have entered are true"))
			if line.driving_license and line.disclaimer_id_details == False:
				raise ValidationError(_("9Please check the desclaimer to ensure that the details you have entered are true"))
			if line.experience and line.disclaimer_experience == False:
				raise ValidationError(_("10Please check the desclaimer to ensure that the details you have entered are true"))
			if line.pan_number and line.disclaimer_id_details == False:
				raise ValidationError(_("11Please check the desclaimer to ensure that the details you have entered are true"))
			if line.passport_id and line.disclaimer_id_details == False:
				raise ValidationError(_("12Please check the desclaimer to ensure that the details you have entered are true"))
			if line.years_experience and line.disclaimer_experience == False:
				raise ValidationError(_("13Please check the desclaimer to ensure that the details you have entered are true"))

	# if 'self_declare_edit' in vals:
	# 	if self.self_declare_edit == 'no':
	# 		self_declaration_add = self.env.ref('hr_employee_kra.group_self_declaration_not_create')
	# 		self_declaration_add.write({'users': [(4, self.user_id.id)]})
	# 	elif self.self_declare_edit == 'yes':
	# 		self_declaration_add = self.env.ref('hr_employee_kra.group_self_declaration_not_create')
	# 		self_declaration_add.write({'users': [(3, self.user_id.id)]})


	###Self Declaration Active Edit access disabled after two months from joining date
	@api.multi
	def _self_declare_edit_active_two_months(self):
		today = date.today()
		domain_month = today + relativedelta(months=-2)
		for record in self.sudo().search([('joining_date', '=', domain_month)]):
				if record.self_declare_edit == 'yes':
					self_declaration_add = record.env.ref('hr_employee_kra.group_self_declaration_not_create')
					record.sudo().write({'self_declare_edit': 'no'})
					self_declaration_add.sudo().write({'users': [(3, record.user_id.id)]})


	###Self Declaration Active Edit access enabled on April month<
	@api.multi
	def _self_declare_edit_active_april_month(self):
		for record in self.sudo().search([('self_declare_edit', '=', 'no')]):
			if record:
				self_declaration_add = record.env.ref('hr_employee_kra.group_self_declaration_not_create')
				self_declaration_add.sudo().write({'users': [(4, record.user_id.id)]})
				record.sudo().write({'self_declare_edit': 'yes'})


	###Self Declaration Dective Edit access dissabled on June Month<
	@api.multi
	def _self_declare_edit_deactive(self):
		for record in self.sudo().search([('self_declare_edit', '=', 'yes')]):
			if record:
				self_declaration_add = record.env.ref('hr_employee_kra.group_self_declaration_not_create')
				self_declaration_add.sudo().write({'users': [(3, record.user_id.id)]})
				record.sudo().write({'self_declare_edit': 'no'})

	###Self Declaration Active Document access enabled on 15 Dec<
	@api.multi
	def _self_declare_document_active_dec_month(self):
		for record in self.sudo().search([('self_declare_document', '=', 'no')]):
			if record:
				record.sudo().write({'self_declare_document': 'yes'})


	###Self Declaration Dective Document access dissabled on 16-Jan Month<
	@api.multi
	def _self_declare_document_deactive(self):
		for record in self.sudo().search([('self_declare_document', '=', 'yes')]):
			if record:
				record.sudo().write({'self_declare_document': 'no'})

	@api.multi	
	@api.constrains('active')
	def _check_active(self):
		if self.active == False:
			self.user_id.sudo().write({'active':False})
		if self.active == True:
			self.user_id.sudo().write({'active':True})

	@api.multi
	def _compute_is_hr(self):
		user_group= self.env['res.users'].has_group('hr_employee_kra.group_kra_hr')
		# employee_group = self.env['res.users'].has_group('hr_employee_kra.group_kra_user')
		var = self.env.uid

		for rec in self:
			if rec.user_id.id == var:
				rec.is_employee = True
			if user_group:
				rec.is_hr = True

	@api.model
	@api.onchange('is_hr')
	def _check_user(self):
		user_group = self.env['res.users'].has_group('hr_employee_kra.group_kra_hr')
		if user_group:
			self.is_hr = True
		else:
			self.is_hr = False

	@api.depends('joining_date')
	def _compute_confirmation(self):
		for rec in self:
			if not rec.probation_eval_date:
				if rec.joining_date:
					var = rec.joining_date + relativedelta(days=-1, months=6)
					# print("AAA", var)
					rec.probation_eval_date = var

	@api.multi
	def confirm(self):
		self.write({'state':'to_approve'})

	@api.multi
	def approve(self):
		self.write({'state':'approved'})

	@api.multi
	def reset(self):
		self.write({'state':'draft'})

	@api.multi
	@api.onchange('employment_status')
	def onchange_employment_status(self):
		for vals in self:
			if vals.employment_status and vals.emp_confirmation_date:
				today_date = datetime.strptime(time.strftime('%Y-%m-15'), '%Y-%m-%d').date()
				if vals.employment_status and vals.emp_confirmation_date:
					if vals.employment_status == 'confirmed':
						el_leave = self.env['hr.leave.type'].search([('name', '=', 'EL'),('company_id', '=',vals.company_id.id)])
						if el_leave:
							el_leaves_id = self.env['hr.leave.allocation'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', el_leave.id)],limit=1)
							if el_leaves_id and vals.emp_confirmation_date <= today_date:
								start_date = date.today().replace(day=1)
								end_date = date.today().replace(day=1) + relativedelta(months=1) - timedelta(1)
								for el_id in el_leaves_id:
									if el_id.el_sl_date:
										if el_id.el_sl_date >= start_date and el_id.el_sl_date <= end_date:
											continue
										else:
											el_count = el_id.number_of_days+1
											el_id.write({'number_of_days':el_count,'el_sl_date':date.today()})
									elif self.emp_confirmation_date >= start_date and self.emp_confirmation_date <= today_date:
										el_count = el_id.number_of_days+1
										el_id.write({'number_of_days':el_count,'el_sl_date':date.today()})
						sl_leave = self.env['hr.leave.type'].search([('name', '=', 'SL'),('company_id', '=',self.company_id.id)])
						if sl_leave:
							sl_leaves_id = self.env['hr.leave.allocation'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)],limit=1)
							if sl_leaves_id:
								start_date = date.today().replace(day=1)
								end_date = date.today().replace(day=1) + relativedelta(months=1) - timedelta(1)
								count_days = 0
								for sl_id in sl_leaves_id:
									if sl_id.el_sl_date:
										if sl_id.el_sl_date >= start_date and sl_id.el_sl_date <= end_date:
											continue
										elif vals.emp_confirmation_date >= start_date and vals.emp_confirmation_date <= today_date:
											for leave in self.env['hr.leave'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)]):
												count_days += leave.number_of_days
											sl_count = count_days+1
											sl_id.write({'number_of_days':sl_count,'el_sl_date':date.today()})
										elif vals.emp_confirmation_date > today_date:
											for leave in self.env['hr.leave'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)]):
												count_days += leave.number_of_days
											sl_count = count_days
											sl_id.write({'number_of_days':sl_count,'el_sl_date':date.today()})
									elif vals.emp_confirmation_date >= start_date and vals.emp_confirmation_date <= today_date:
										for leave in self.env['hr.leave'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)]):
											count_days += leave.number_of_days
										sl_count = count_days+1
										sl_id.write({'number_of_days':sl_count,'el_sl_date':date.today()})
									elif vals.emp_confirmation_date > today_date:
										for leave in self.env['hr.leave'].sudo().search([('employee_id.employee_id', '=', self.employee_id),('state', '=', 'validate'),('holiday_status_id', '=', sl_leave.id)]):
											count_days += leave.number_of_days
										sl_count = count_days
										sl_id.write({'number_of_days':sl_count,'el_sl_date':date.today()})


	@api.multi
	def hr_approval_unblock(self):
		form_view = self.env.ref('eci_employee_custom.form_unblock_remark_wizard')
		return {
			'name': "Unblock Remarks",
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': form_view.id,
			'res_model': 'unblock.remark.wizard',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
				'employee_id': self.ids, 'is_hr': True
			}
		}

	@api.model
	def create(self, vals):
		res = super(HrEmployee, self).create(vals)
		if res:
			# create user when create employee
			user_id = self.env['res.users'].create({
				'name': res.name,
				'login': res.employee_id or res.work_email,
				'email': res.work_email or res.employee_email,
				'password': 'Sigma@1',
				'groups_id': [(6, 0, [self.env.ref('hr_employee_kra.group_kra_user').id,
									  self.env.ref('account.group_account_invoice').id, 
									  # self.env.ref('hr_recruitment.group_hr_recruitment_user').id, 
									  self.env.ref('hr_timesheet.group_hr_timesheet_user').id, 
									  self.env.ref('hr_attendance.group_hr_attendance').id, 
									  self.env.ref('hr_payroll.group_hr_payroll_user').id,
									  self.env.ref('base.group_erp_manager').id])]
			})
			
			app_1 = self.env['res.users'].search([('id', '=', res.lone_manager_id.user_id.id),('company_id', '=', self.company_id.id)])
			app_2 = self.env['res.users'].search([('id', '=', res.ltwo_manager_id.user_id.id),('company_id', '=', self.company_id.id)])
			app_3 = self.env['res.users'].search([('id', '=', res.hod_id.user_id.id),('company_id', '=', self.company_id.id)])
			app_4 = self.env['res.users'].search([('id', '=', res.parent_id.user_id.id),('company_id', '=', self.company_id.id)])
			if res.lone_manager_id:
				var = res.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
				# print("AAA", var)
				var_two = res.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
				var_hod = res.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
				var_director = res.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
				if not var:
					if var_two:
						app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
						# print("BBBB", var_2)
					elif var_hod:
						app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
						# print("CCC", var_3)
					elif var_director:
						app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
						# print("DDD", var_4)
					else:
						app_1.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_approver_1').id,
													  self.env.ref('account.group_account_manager').id,
													  self.env.ref('hr.group_hr_manager').id,
													  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
													  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
													  self.env.ref('hr_timesheet.group_timesheet_manager').id,
													  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
													  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
													  self.env.ref('base.group_erp_manager').id])]
					})
			if res.ltwo_manager_id:
				var = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
				var_two = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
				var_hod = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
				var_director = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
				if not var_two:
					if var:
						app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
						# print("CCC", var)
					elif var_hod:
						app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
					elif var_director:
						app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
					else:
						app_2.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_approver_2').id,
							           				  self.env.ref('account.group_account_manager').id,
													  self.env.ref('hr.group_hr_manager').id,
													  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
													  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
													  self.env.ref('hr_timesheet.group_timesheet_manager').id,
													  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
													  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
													  self.env.ref('base.group_erp_manager').id])]
						})
			if res.hod_id:
				var = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
				var_two = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
				var_hod = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
				var_director = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
				if not var_hod:
					if var:
						app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_hod').id)]})
						# print("DDD", var)
					elif var_two:
						app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_hod').id)]})
						# print("EEE", var_2)
					elif var_director:
						app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.groups_kra_hod').id)]})
					else:
						app_3.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_hod').id,
													  self.env.ref('account.group_account_manager').id,
													  self.env.ref('hr.group_hr_manager').id,
													  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
													  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
													  self.env.ref('hr_timesheet.group_timesheet_manager').id,
													  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
													  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
													  self.env.ref('base.group_erp_manager').id])]
						})
			if res.parent_id:
				var = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
				var_two = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
				var_hod = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
				var_director = res.ltwo_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
				if not var_director:
					if var:
						app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
						# print("FFF", var)
					elif var_two:
						app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
					elif var_hod:
						app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
					else:
						app_4.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_director').id,
												  self.env.ref('account.group_account_manager').id,
												  self.env.ref('hr.group_hr_manager').id,
												  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
												  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
												  self.env.ref('hr_timesheet.group_timesheet_manager').id,
												  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
												  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
												  self.env.ref('base.group_erp_manager').id])]
						})


			if user_id:
				res.user_id = user_id
				# template_id = self.env.ref('eci_employee_custom.email_template_create_user')
				# template_id.sudo().send_mail(res.id, force_send=True)
		if res.attendance_type and res.user_id:
			mobile_group = res.user_id.has_group('attendance_custom.group_mobile_attendance')
			geofence_group = res.user_id.has_group('attendance_custom.group_geofence_attendance')
			if not mobile_group and res.attendance_type == 'mobile_app':
				mobile_add = self.env.ref('attendance_custom.group_mobile_attendance')
				mobile_add.sudo().write({'users': [(4, res.user_id.id)]})
			elif mobile_group and res.attendance_type != 'mobile_app' :
				mobile_remove = self.env.ref('attendance_custom.group_mobile_attendance')
				mobile_remove.sudo().write({'users': [(3, res.user_id.id)]})

			if not geofence_group and res.attendance_type == 'geo_fence':
				mobile_add = self.env.ref('attendance_custom.group_geofence_attendance')
				mobile_add.sudo().write({'users': [(4, res.user_id.id)]})
			elif geofence_group and res.attendance_type != 'geo_fence':
				mobile_remove = self.env.ref('attendance_custom.group_geofence_attendance')
				mobile_remove.sudo().write({'users': [(3, res.user_id.id)]})
		if res.timesheet:
			if res.timesheet == 'no':
				timesheet_add = self.env.ref('hr_timesheet_extended.group_timesheet_not_create')
				timesheet_add.sudo().write({'users': [(3, res.user_id.id)]})
		if res.employee_id:
			res.sudo().write({'self_declare_edit': 'yes'})
			if res.self_declare_edit == 'yes':
				self_declaration_add = self.env.ref('hr_employee_kra.group_self_declaration_not_create')
				self_declaration_add.sudo().write({'users': [(3, res.user_id.id)]})
		# Code for allocate leaves when create probation employee
		if res.employment_status == 'probation':
			sl_leave = self.env['hr.leave.type'].search([('name', '=', 'SL')])
			if sl_leave:
				sl_id = self.env['hr.leave.allocation'].create({
					'name': 'SL Leave ' + str(datetime.now().month) + str(datetime.now().year),
					'holiday_status_id': sl_leave.id,
					'number_of_days': 3,
					'holiday_type': 'employee',
					'el_sl_date' : date.today(),
					'employee_id': res.id
				})
				if sl_id:
					sl_id.action_approve()
					if sl_leave.validation_type == 'both':
						sl_id.action_validate()
			el_leave = self.env['hr.leave.type'].search([('name', '=', 'EL')])
			if el_leave:
				el_id = self.env['hr.leave.allocation'].create({
					'name': 'EL Leave ' + str(datetime.now().month) + str(datetime.now().year),
					'holiday_status_id': el_leave.id,
					'number_of_days': 0,
					'holiday_type': 'employee',
					'el_sl_date' : date.today(),
					'employee_id': res.id
				})
				if el_id:
					el_id.action_approve()
					if el_leave.validation_type == 'both':
						el_id.action_validate()
			pl_leave = self.env['hr.leave.type'].search([('name', '=', 'PL')])
			if pl_leave:
				pl_id = self.env['hr.leave.allocation'].create({
					'name': 'PL Leave ' + str(datetime.now().month) + str(datetime.now().year),
					'holiday_status_id': pl_leave.id,
					'number_of_days': 0,
					'holiday_type': 'employee',
					'pl_date' : date.today(),
					'employee_id': res.id
				})
				if pl_id:
					pl_id.action_approve()
					if pl_leave.validation_type == 'both':
						pl_id.action_validate()
		return res

	@api.multi
	def write(self, vals):
		res = super(HrEmployee, self).write(vals)
		app_1 = self.env['res.users'].search([('id', '=', self.lone_manager_id.user_id.id),('company_id', '=', self.company_id.id)])
		app_2 = self.env['res.users'].search([('id', '=', self.ltwo_manager_id.user_id.id),('company_id', '=', self.company_id.id)])
		app_3 = self.env['res.users'].search([('id', '=', self.hod_id.user_id.id),('company_id', '=', self.company_id.id)])
		app_4 = self.env['res.users'].search([('id', '=', self.parent_id.user_id.id),('company_id', '=', self.company_id.id)])
		if self.lone_manager_id:
			var = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
			var_two = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
			var_hod = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
			var_director = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			if not var:
				if var_two:
					app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
					# print("BBBB", var_2)
				elif var_hod:
					app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
					# print("BBBB", var_3)
				elif var_director:
					app_1.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_1').id)]})
					# print("BBBB", var_4)
				else:
					app_1.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_approver_1').id,
												  self.env.ref('account.group_account_manager').id,
												  self.env.ref('hr.group_hr_manager').id,
												  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
												  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
												  self.env.ref('hr_timesheet.group_timesheet_manager').id,
												  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
												  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
												  self.env.ref('base.group_erp_manager').id])]
				})
		if self.ltwo_manager_id:
			var = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
			var_two = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
			var_hod = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
			var_director = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			if not var_two:
				if var:
					app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
					# print("CCC", var)
				elif var_hod:
					app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
				elif var_director:
					app_2.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_approver_2').id)]})
				else:
					app_2.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_approver_2').id,
												  self.env.ref('account.group_account_manager').id,
												  self.env.ref('hr.group_hr_manager').id,
												  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
												  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
												  self.env.ref('hr_timesheet.group_timesheet_manager').id,
												  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
												  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
												  self.env.ref('base.group_erp_manager').id])]
					})
		if self.hod_id:
			var = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
			var_two = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
			var_hod = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
			var_director = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			if not var_hod:
				if var:
					app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_hod').id)]})
					# print("DDD", var)
				elif var_two:
					app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_hod').id)]})
					# print("EEE", var_2)
				elif var_director:
					app_3.write({'groups_id': [(4, self.env.ref('hr_employee_kra.groups_kra_hod').id)]})
				else:
					app_3.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_hod').id,
												  self.env.ref('account.group_account_manager').id,
												  self.env.ref('hr.group_hr_manager').id,
												  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
												  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
												  self.env.ref('hr_timesheet.group_timesheet_manager').id,
												  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
												  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
												  self.env.ref('base.group_erp_manager').id])]
					})
		if self.parent_id:
			var = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_1')
			var_two = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_approver_2')
			var_hod = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_hod')
			var_director = self.lone_manager_id.user_id.has_group('hr_employee_kra.group_kra_director')
			if not var_director:
				if var:
					app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
					# print("FFF", var)
				elif var_two:
					app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
				elif var_hod:
					app_4.write({'groups_id': [(4, self.env.ref('hr_employee_kra.group_kra_director').id)]})
				else:
					app_4.write({'groups_id': [(6,0, [self.env.ref('hr_employee_kra.group_kra_director').id,
											  self.env.ref('account.group_account_manager').id,
											  self.env.ref('hr.group_hr_manager').id,
											  self.env.ref('hr_holidays.group_hr_holidays_manager').id,
											  # self.env.ref('hr_recruitment.group_hr_recruitment_manager').id,
											  self.env.ref('hr_timesheet.group_timesheet_manager').id,
											  self.env.ref('hr_attendance.group_hr_attendance_manager').id,
											  self.env.ref('hr_payroll.group_hr_payroll_manager').id,
											  self.env.ref('base.group_erp_manager').id])]
					})
		ramp = self.env['res.users'].sudo().search([('employee_ids', 'in', self.ids)])
		for rar in ramp:
			# print("RAMP", ramp)
			var_1 = self.env['res.partner'].sudo().search([('user_ids', 'in', ramp.ids)])
			for res in var_1:
				# print("RES", var_1)
				res.write({'email': self.work_email})


		if 'attendance_type' in vals and self.user_id:
			mobile_group = self.user_id.has_group('attendance_custom.group_mobile_attendance')
			geofence_group = self.user_id.has_group('attendance_custom.group_geofence_attendance')
			if not mobile_group and self.attendance_type == 'mobile_app':
				mobile_add = self.env.ref('attendance_custom.group_mobile_attendance')
				mobile_add.sudo().write({'users': [(4, self.user_id.id)]})
			elif mobile_group and self.attendance_type != 'mobile_app' :
				mobile_remove = self.env.ref('attendance_custom.group_mobile_attendance')
				mobile_remove.sudo().write({'users': [(3, self.user_id.id)]})

			if not geofence_group and self.attendance_type == 'geo_fence':
				mobile_add = self.env.ref('attendance_custom.group_geofence_attendance')
				mobile_add.sudo().write({'users': [(4, self.user_id.id)]})
			elif geofence_group and self.attendance_type != 'geo_fence':
				mobile_remove = self.env.ref('attendance_custom.group_geofence_attendance')
				mobile_remove.sudo().write({'users': [(3, self.user_id.id)]})
		if 'timesheet' in vals:
			if self.timesheet == 'no':
				timesheet_add = self.env.ref('hr_timesheet_extended.group_timesheet_not_create')
				timesheet_add.sudo().write({'users': [(4, self.user_id.id)]})
			elif self.timesheet == 'yes':
				timesheet_remove = self.env.ref('hr_timesheet_extended.group_timesheet_not_create')
				timesheet_remove.sudo().write({'users': [(3, self.user_id.id)]})
		if 'self_declare_edit' in vals:
			if self.self_declare_edit == 'no':
				self_declaration_add = self.env.ref('hr_employee_kra.group_self_declaration_not_create')
				self_declaration_add.sudo().write({'users': [(4, self.user_id.id)]})
			elif self.self_declare_edit == 'yes':
				self_declaration_add = self.env.ref('hr_employee_kra.group_self_declaration_not_create')
				self_declaration_add.sudo().write({'users': [(3, self.user_id.id)]})
		return res
