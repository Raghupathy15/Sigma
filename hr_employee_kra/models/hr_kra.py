# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class HrKra(models.Model):
	_name = 'hr.kra'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_order = 'id desc'

	@api.depends('kra_line_ids.target')
	def _compute_total(self):
		for line in self:
			total = 0
			for lines in line.kra_line_ids:
				total += lines.target
			if total: 
				line.update({'total_weightage':total})


	kra_line_ids = fields.One2many('hr.kra.line','kra_id',copy=True)
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now())
	name = fields.Char(required=True, store=True,copy=False, string='Seq No.', readonly=True, index=True, default=lambda self: _('New'))
	particular_user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.uid)
	employee_id = fields.Many2one('hr.employee',string="Employee Name",store=True,track_visibility='onchange',domain="([('lone_manager_id.user_id','=',particular_user_id)])")
	resignation_id = fields.Many2one('hr.resignation',string="Resignation")
	employee_code = fields.Char(string="Employee Id",related="employee_id.employee_id",store=True)
	date_of_joining = fields.Date(string="Date of Joining",related="employee_id.joining_date",store=True)
	
	department = fields.Many2one('hr.department',string="Department",related="employee_id.department_id",store=True)
	work_location = fields.Many2one('work.location',string="Work Location",related="employee_id.location_work_id",store=True)
	# state = fields.Selection([('draft','Draft'),('kra_created','KRA Created'),('reject','Disagreed by Approver 1'),('reject_by_emp','Disagreed by Employeee'),('revised','Revised'),('resubmitted','Resubmitted'),('employee','Approved by Approver 2'),('done','Done')],string="Stage",default='draft')
	state = fields.Selection([('draft','Draft'),('kra_created','KRA Created'),('employee','Approved by Approver 2'),('reject','Disagreed by Approver 2'),('revised','Revised'),('resubmitted','Resubmitted'),('reject_by_emp','Disagreed by Employeee'),('done','Done')],string="Stage",default='draft',track_visibility='onchange')
	# reason_l1_manager = fields.Text('Reason For L1')
	reason_l2_manager = fields.Text('Approver 2 Remarks',track_visibility='onchange')
	reason_by_employee = fields.Text('Employee Remarks',track_visibility='onchange')
	kra_created_date = fields.Date(string="Doc Date",store=True,default=lambda self:fields.date.today())
	
	document_created_by = fields.Many2one('res.users', string='Created User', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.uid ,store=True)
	user_id = fields.Many2one('res.users', string='Related User', index=True, track_visibility='onchange', track_sequence=2, related="employee_id.user_id")
	objective = fields.Text(string="Objective")
	total_weightage = fields.Float(string="Total Weightage",compute="_compute_total",store=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('hr.kra'))

	reporting_manager = fields.Many2one('hr.employee',string="Approver1",related="employee_id.lone_manager_id",store=True,track_visibility='onchange')
	reporting_manager_user_id = fields.Many2one('res.users',string="Reporting Manager User Id",related="employee_id.lone_manager_id.user_id",store=True)
	l2_manager = fields.Many2one('hr.employee',string="Approver 2",related="employee_id.ltwo_manager_id",store=True,track_visibility='onchange')
	l2_manager_user_id = fields.Many2one('res.users',string="Approver 2 User Id",related="employee_id.ltwo_manager_id.user_id",store=True)
	l1_confirm_date = fields.Datetime(string='A1 Updated', track_visibility='onchange', track_sequence=2)
	l2_accept_date = fields.Datetime(string='A2 Accepted', track_visibility='onchange', track_sequence=2)
	l2_reject_date = fields.Datetime(string='A2 Rejected', track_visibility='onchange', track_sequence=2)
	l1_resubmit_date = fields.Datetime(string='A1 Resubmitted', track_visibility='onchange', track_sequence=2)
	emp_accept_date = fields.Datetime(string='Employee Accepted', track_visibility='onchange', track_sequence=2)
	emp_rejected_date = fields.Datetime(string='Employee Rejected', track_visibility='onchange', track_sequence=2)

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

	@api.depends('reporting_manager_user_id','employee_id')
	def compute_approver1(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for line in self:
			if line.employee_id:
				if line.reporting_manager_user_id.id == current_employee and is_approver_1:
					line.is_applover_l1 = True
				else:
					line.is_applover_l1 = False
				if line.l2_manager_user_id.id == current_employee and is_approver_2:
					line.is_applover_l2 = True
				else:
					line.is_applover_l2 = False
				if line.user_id.id == current_employee:
					line.is_employee = True
				else:
					line.is_employee = False
				if line.reason_l2_manager:
					line.is_l2_reason = True
				else:
					line.is_l2_reason = False
				if line.reason_by_employee:
					line.is_employee_reason = True
				else:
					line.is_employee_reason = False
				if line.employee_id:
					line.is_employee_true = True
				else:
					line.is_employee_true = False


	is_applover_l1 = fields.Boolean('Approver 1', compute="compute_approver1", default=False)
	is_applover_l2 = fields.Boolean('Approver 2', compute="compute_approver1", default=False)
	is_employee = fields.Boolean('Employee 1', compute="compute_approver1", default=False)
	is_l2_reason = fields.Boolean('Employee 1', compute="compute_approver1", default=False)
	is_employee_reason = fields.Boolean('Employee 1', compute="compute_approver1", default=False)
	is_employee_true = fields.Boolean('Employee 1', compute="compute_approver1", default=False)

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('hr.kra')
		res = super(HrKra, self).create(vals)
		return res

	@api.constrains('total_weightage')
	def _check_total_weightage(self):
		for line in self:
			if line.total_weightage > 100:
				raise ValidationError("Your Total weightage is greater than 100 : ")
			if line.total_weightage < 100:
				raise ValidationError("Your Total weightage is lesser than 100: ")

	@api.multi
	def l1_confirm(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if line.reporting_manager_user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Update this document.'))
			if line.reporting_manager_user_id.id == current_employee and is_approver_1:
				line.write({'state': 'kra_created','l1_confirm_date': datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_update_kra')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'KRA is created for employee',
					'employee_id': line.employee_id.id, 'model_name': 'hr.kra',
					'approver_ids': [(6, 0, line.hr_reminder_approver2_ids.ids)],
					'hr_kra_id': line.id
				})


	@api.onchange('employee_id')
	def onchange_kra(self):
		create_probation = self.env['hr.kra'].search([('employee_id', '=', self.employee_id.id)])
		if create_probation:
			raise UserError(_('Already KRA Created for this Employee.'))

	@api.multi
	def resubmit(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if line.reporting_manager_user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Resubmit this document.'))
			if line.reporting_manager_user_id.id == current_employee and is_approver_1:
				line.write({'state': 'resubmitted','l1_resubmit_date': datetime.now()})

	@api.multi
	def l2_accept(self):
		current_employee = self.env.uid
		is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for line in self:
			if line.l2_manager_user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Accept this document.'))
			if line.l2_manager_user_id.id == current_employee and is_approver_2:
				line.write({'state': 'employee','l2_accept_date': datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_app_kra')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'Key Result Areas/Goals are created by your manager',
					'employee_id': line.employee_id.id, 'model_name': 'hr.kra',
					'approver_ids': [(6, 0, line.employee_ids.ids)],
					'hr_kra_id': line.id
				})

	@api.multi
	def l2_reject(self):
		current_employee = self.env.uid
		is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for line in self:
			if line.l2_manager_user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Disagree this document.'))
			if line.l2_manager_user_id.id == current_employee and is_approver_2:
				# line.write({'state': 'reject','l2_reject_date': datetime.now()})
				form_view = self.env.ref('hr_employee_kra.form_kra_remark_wizard')
				return {
		            'name': "Remarks",
		            'view_mode': 'form',
		            'view_type': 'form',
		            'view_id': form_view.id,
		            'res_model': 'kra.remark',
		            'type': 'ir.actions.act_window',
		            'target': 'new',
		            'context': {
		                'kra_id': self.ids, 'is_reject': True
		            }
		        }

	@api.multi
	def emp_accept(self):
		current_employee = self.env.uid
		is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for lines in self:
			if lines.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Accept this document.'))
			if lines.user_id.id == current_employee and is_user:
				lines.write({'state': 'done','emp_accept_date': datetime.now()})
				# for val in self:
				# 	quarterly = self.env['kra.quarterly'].create({
				# 	'state': 'draft',
				# 	'employee_id': val.employee_id.id,
				# 	'employee_code': val.employee_code,
				# 	'doj': val.date_of_joining,
				# 	'manager_id': val.reporting_manager.id,
				# 	'kra_id': val.id,
				# 	})
				# 	for line in self.kra_line_ids:
				# 		quarterly_line = self.env['quarterly.review'].create({
				# 		'kra': line.name or False,
				# 		'details_kra': line.details,
				# 		'timeline': line.timeline_id,
				# 		'weightage': line.target,
				# 		'review_id': quarterly.id,
				# 		'state':'draft',
				# 		})
		return True

	@api.multi
	def emp_reject(self):
		current_employee = self.env.uid
		is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for lines in self:
			if lines.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Disagree this document.'))
			if lines.user_id.id == current_employee and is_user:
				# lines.write({'state': 'reject_by_emp','emp_rejected_date': datetime.now()})
				form_view = self.env.ref('hr_employee_kra.form_kra_emp_remark_wizard')
				return {
		            'name': "Employee Remarks",
		            'view_mode': 'form',
		            'view_type': 'form',
		            'view_id': form_view.id,
		            'res_model': 'kra.emp.remark',
		            'type': 'ir.actions.act_window',
		            'target': 'new',
		            'context': {
		                'kra_id': self.ids, 'is_reject': True
		            }
		        }

	@api.multi
	def reset_to_draft(self):
		self.state = 'draft'

class HrKraLine(models.Model):
	_name = 'hr.kra.line'

	kra_id = fields.Many2one('hr.kra')
	name = fields.Char(string="Key Result Area")
	details = fields.Char(string="Details of Key Result Area")
	timeline_id = fields.Many2one('timeline.master', string="Timeline")
	time_line = fields.Selection([('daily', 'Daily'),
                                  ('weekly', 'Weekly'),
                                  ('monthly', 'Monthly'),
                                  ('as&when', 'As & When'),
                                  ('annually', 'Annually'),
                                  ('quarterly', 'quarterly'),
                                  ('regular', 'Regular')],
                                  string="Timeline")
	target = fields.Integer(string="Weightage (%)")