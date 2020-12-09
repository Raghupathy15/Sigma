# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
date_format = "%Y-%m-%d"


class HrResignation(models.Model):
	_name = 'hr.resignation'
	_inherit = 'mail.thread'
	# _rec_name = 'employee_id'
	_order = 'id desc'

	def _get_employee_id(self):
		# assigning the related employee of the logged in user
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	@api.multi
	def compute_default_employee(self):
		master = self.env['exit.clearance.master'].sudo().search([('active','=',True)])
		rec = ''
		for emp_ids in master:
			rec = emp_ids.employee_id
			self.depart_employees_ids = rec.ids

	name = fields.Char(string='Seq No', required=True, copy=False, readonly=True, index=True,
					   default=lambda self: _('New'))
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now())
	employee_id = fields.Many2one('hr.employee', string="Employee", default=_get_employee_id,
								  help='Name of the employee for whom the request is creating')
	employee_code = fields.Char(string="Employee Code", related="employee_id.employee_id", store=True, readonly=False)
	manager_id = fields.Many2one('hr.employee', 'Approver1', related="employee_id.lone_manager_id", readonly=False)
	l2_manager_id = fields.Many2one('hr.employee',string="Approver2",related="employee_id.ltwo_manager_id")
	department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
									help='Department of the employee')
	job_id = fields.Many2one('employee.designation', string="Designation", related='employee_id.designation_id',
									help='Designation of the employee')
	joined_date = fields.Date(string="DOJ",
							  help='Joining date of the employee', related="employee_id.joining_date")
	expected_revealing_date = fields.Date(string="Requested Relieving Date",
										  help='Date on which he is revealing from the company', required=True)
	resign_confirm_date = fields.Date(string="Resignation date",default=lambda self: fields.date.today())
	approved_revealing_date = fields.Date(string="Approved Relieving Date", help='The date approved for the relieving')
	approver_reason = fields.Text(string="Approver Remarks", help='Specify reason for leaving the company')
	location_work_id = fields.Many2one('work.location', string="Work Location",related="employee_id.location_work_id",track_visibility='always')
	reason = fields.Text(string="Employee Remarks", help='Specify reason for leaving the company',required=True)
	notice_period = fields.Char(string="Notice Period", compute='_notice_period')
	state = fields.Selection([('draft','Draft'), ('confirm','Pending'),('approved','Approved'),
							('reject','Disagreed'),('cancel_req','Cancel Request'),('cancel','Cancelled')], string='Status', default='draft')
	user_id = fields.Many2one('res.users', string='Related User', index=True, track_visibility='onchange', track_sequence=2, related="employee_id.user_id",store=True)
	is_employee = fields.Boolean('Empoyee user', compute="compute_user")
	is_approver1 = fields.Boolean('Approver 1', compute="compute_user")
	send_mail=fields.Boolean('Send mail')
	cancel_res=fields.Text('Cancel Remarks')
	mail = fields.Boolean('Send mail')
	is_confirm = fields.Boolean('Confirm', compute="compute_buttons")
	depart_employees_ids = fields.Many2many('hr.employee',string="Department Employees",compute="compute_default_employee")

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


	@api.onchange('approved_revealing_date')
	def onchange_app_revealing_date(self):
		employee = self.env['hr.employee'].sudo().search([('id', '=',self.employee_id.id)])
		if self.approved_revealing_date and employee:
			# employee.write({'exit_date':self.approved_revealing_date})
			self.send_mail = False
			self.mail = True

	@api.multi
	def button_acpt_cancellation(self):	
		employee = self.env['hr.employee'].sudo().search([('id', '=',self.employee_id.id)])
		employee.exit_date = ''
		employee.resignation_date = ''
		employee.payroll = 'yes'
		interview = self.env['kra.exit.intw'].sudo().search([('employee_id', '=',self.employee_id.id)])
		if interview:
			interview.unlink()
		clearance = self.env['exit.clearance'].sudo().search([('employee_id', '=',self.employee_id.id)])
		if clearance:
			clearance.unlink()
		settlement = self.env['final.settlement'].sudo().search([('employee_id', '=',self.employee_id.id)])
		if clearance:
			settlement.unlink()
		self.write({'state':'cancel'})

	@api.multi
	def button_rej_cancel_resignation(self):
		self.write({'state':'confirm'})

	@api.multi
	def button_change_revealing_date(self):
		current_employee = self.env.uid
		employee = self.env['hr.employee'].sudo().search([('id', '=',self.employee_id.id)])
		if self.manager_id.user_id.id != current_employee:
			raise UserError(_('You are not a authorized user to Reject this document.'))
		if self.approved_revealing_date and self.approver_reason and employee and self.send_mail == False:
			employee.write({'exit_date':self.approved_revealing_date})
			if self.mail == True:
				template_id = self.env.ref('hr_resignation.email_template_to_request_date_changed')
				template_id.send_mail(self.id, force_send=True)
				self.write({'send_mail':True,'mail':False})
				# Reminder Notification
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Your Relieving date is changed',
					'employee_id': self.employee_id.id, 'model_name': 'hr.resignation',
					'approver_ids': [(6, 0, self.employee_ids.ids)],
					'hr_resignation_id': self.id
				})

	@api.depends('user_id')
	def compute_buttons(self):
		for vals in self:
			current_employee = vals.env.uid
			if vals.employee_id.user_id.id == current_employee:
				vals.is_confirm = True
			else:
				vals.is_confirm = False 

	@api.depends('user_id')
	def compute_user(self):
		for vals in self:
			l_one = vals.manager_id
			current_employee = vals.env.uid
			if vals.manager_id.user_id.id == current_employee:
				vals.is_approver1 = True
			else:
				vals.is_approver1 = False
			if vals.employee_id.user_id.id == current_employee:
				vals.is_employee = True
			else:
				vals.is_employee = False

	@api.model
	def create(self, vals):
		# assigning the sequence for the record
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
		res = super(HrResignation, self).create(vals)
		return res

	@api.constrains('employee_id')
	def check_employee(self):
		# Checking whether the user is creating leave request of his/her own
		for rec in self:
			if not self.env.user.has_group('hr_employee_kra.group_kra_user'):
				if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
					raise ValidationError(_('You cannot create request for other employees'))

	@api.onchange('employee_id')
	@api.depends('employee_id')
	def check_request_existence(self):
		# Check whether any resignation request already exists
		for rec in self:
			if rec.employee_id:
				resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																		 ('state', 'in', ['confirm', 'approved'])])
				if resignation_request:
					raise ValidationError(_('There is a resignation request in confirmed or'
											' approved state for this employee'))

	@api.multi
	def _notice_period(self):
		# calculating the notice period for the employee
		for rec in self:
			if rec.approved_revealing_date and rec.resign_confirm_date:
				approved_date = datetime.strptime(str(rec.approved_revealing_date), date_format)
				confirmed_date = datetime.strptime(str(rec.resign_confirm_date), date_format)
				notice_period = approved_date - confirmed_date
				rec.notice_period = notice_period.days

	@api.constrains('joined_date', 'expected_revealing_date')
	def _check_dates(self):
		# validating the entered dates
		for rec in self:
			resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																	 ('state', 'in', ['confirm', 'approved'])])
			if resignation_request:
				raise ValidationError(_('There is a resignation request in confirmed or'
										' approved state for this employee'))
			# if rec.joined_date >= rec.expected_revealing_date:
			# 	raise ValidationError(_('Relieving date must be anterior to joining date'))
			if rec.expected_revealing_date < fields.Date.today():
				raise ValidationError(_('Relieving date must be greater than current date'))

	@api.multi
	def confirm_resignation(self):
		current_employee = self.env.uid
		for rec in self:
			if rec.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to confirm this document.'))
			if rec.user_id.id == current_employee:
				rec.state = 'confirm'
				rec.employee_id.resignation_date = fields.Date.today()
				template_id = self.env.ref('hr_resignation.email_template_to_app1')
				template_id.sudo().send_mail(rec.id, force_send=True)
				# Reminder Notification
				hr_reminder = rec.env['hr.reminder'].sudo().create({
					'name': 'Resignation request',
					'employee_id': rec.employee_id.id, 'model_name': 'hr.resignation',
					'approver_ids': [(6, 0, rec.hr_reminder_approver1_ids.ids)],
					'hr_resignation_id': rec.id
				})

	@api.multi
	def cancel_resignation(self):
		for vals in self:
			if not vals.state == 'cancel_req':
				current_employee = vals.env.uid
				if vals.employee_id.user_id.id == current_employee:
					form_view = self.env.ref('hr_resignation.cancel_details_view_id')
					return {
						'name': "Cancel Remarks",
						'view_mode': 'form',
						'view_type': 'form',
						'view_id': form_view.id,
						'res_model': 'cancel.remarks.resignation',
						'type': 'ir.actions.act_window',
						'target': 'new',
						'context': {
							'travel_id': self.ids,
						}
					}
				else:
					raise UserError(_('You are not a authorized user to Reject this document.'))

	@api.multi
	def reject_resignation(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for rec in self:
			if rec.manager_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Reject this document.'))
			if rec.manager_id.user_id.id == current_employee and is_approver_1:
				if not rec.approver_reason:
					raise ValidationError(_('You must give Approver Remarks.'))
				rec.state = 'reject'
				rec.employee_id.exit_date = ''
				rec.employee_id.resignation_date = ''
				template_id = self.env.ref('hr_resignation.email_template_to_employee_rejected')
				template_id.sudo().send_mail(rec.id, force_send=True)
				# Reminder Notification
				hr_reminder = rec.env['hr.reminder'].sudo().create({
					'name': 'Resignation request Rejected',
					'employee_id': rec.employee_id.id, 'model_name': 'hr.resignation',
					'approver_ids': [(6, 0, rec.employee_ids.ids)],
					'hr_resignation_id': rec.id
				})

	@api.multi
	def set_draft(self):
		for rec in self:
			rec.state = 'draft'

	@api.multi
	def approve_resignation(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for rec in self:
			employee = self.env['hr.employee'].search([('employee_id', '=', rec.employee_code)])
			if rec.manager_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Approve this document.'))
			if rec.manager_id.user_id.id == current_employee and is_approver_1:
				if not rec.approved_revealing_date:
					raise ValidationError(_('Enter Approved Relieving Date'))
				if not rec.approver_reason:
					raise ValidationError(_('Enter Approver Remarks'))
				if rec.approved_revealing_date and rec.resign_confirm_date:
					if rec.approved_revealing_date <= rec.resign_confirm_date:
						raise ValidationError(_('Approved relieving date must be anterior to confirmed date'))
					else:
						self.employee_id.exit_date = self.approved_revealing_date
					for val in rec:
						exit = self.env['kra.exit.intw'].create({
						'state': 'draft',
						'employee_id': val.employee_id.id,
						'resignation_id': val.id,
						})
					for clear in rec:
						exit = self.env['exit.clearance'].create({
						'state': 'draft',
						'employee_id': clear.employee_id.id,
						'resignation_id': clear.id,
						'app_releving_date': clear.approved_revealing_date,
						})
					# employee.write({'resignation_date': rec.approved_revealing_date})
					rec.state = 'approved'
					rec.employee_id.payroll = 'no'
					# Mail to Employee if resignation request is approved
					template_id = self.env.ref('hr_resignation.email_template_to_request_approved')
					template_id.sudo().send_mail(rec.id, force_send=True)
					# Reminder Notification
					hr_reminder = rec.env['hr.reminder'].sudo().create({
						'name': 'Resignation request Approved',
						'employee_id': rec.employee_id.id, 'model_name': 'hr.resignation',
						'approver_ids': [(6, 0, rec.employee_ids.ids)],
						'hr_resignation_id': rec.id
					})
					#  Mail to HR, IT & Accounts if resignation request is approved
					template_id = self.env.ref('hr_resignation.email_template_to_all_departments')
					for mail_to in rec.depart_employees_ids:
						for mail in mail_to:
							template_id.sudo().write({'email_to':mail.work_email})
							template_id.sudo().send_mail(rec.id, force_send=True)


	@api.multi
	def update_employee_status(self):
		resignation = self.env['hr.resignation'].search([('state', '=', 'approved')])
		for rec in resignation:
			if rec.approved_revealing_date <= fields.Date.today() and rec.employee_id.active:
				rec.employee_id.active = False
				rec.employee_id.resign_date = rec.approved_revealing_date


class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	resign_date = fields.Date('Resign Date', readonly=True)
