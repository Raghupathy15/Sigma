# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

class HrInductionMaster(models.Model):
	_name = 'hr.induction.master'
	_inherit = ['mail.thread']
	_description = 'Induction Master'



	name = fields.Char(string="Particulars")
	session_details = fields.Char(string="Session Details")
	responsibility = fields.Many2one('hr.department',string="Session Taken by/Responsibility")
	active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the induction master without removing it.")
	induction_master_created_date = fields.Datetime(string="Induction Master Created",default=lambda self: fields.datetime.now(),track_visibility='onchange',readonly=True)



class HrInduction(models.Model):
	_name = 'hr.induction'
	_description = "Induction"
	_inherit = ['mail.thread']
	_order = 'id desc'

	@api.model
	def _default_induction_line(self):
		master = self.env['hr.induction.master']
		vals = []
		master_ids = master.search([])

		for line in master_ids:
			data={}
			data['session_details'] = line.session_details
			data['name'] = line.name
			data['responsibility'] = line.responsibility.id
			vals.append((0,0,data))
		return vals

	@api.model
	def default_get(self, fields):
		res = super(HrInduction, self).default_get(fields)
		emp_user_id = self.env.uid
		created_hr_employee_id = self.env['hr.employee'].search([('user_id', '=', emp_user_id)])
		if created_hr_employee_id:
			res['created_hr_employee_id'] = created_hr_employee_id.id
		return res

	name = fields.Char(string="Seq No.",track_visibility='onchange')
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now())
	induction_created_date = fields.Date(string="Doc Date",default=lambda self: fields.date.today(),track_visibility='onchange',readonly=True)
	employee_id = fields.Many2one('hr.employee',string="Employee Name",track_visibility='onchange',required=True)
	employee_code = fields.Char(string="Employee Id",related="employee_id.employee_id",store=True)
	date_of_joining = fields.Date(string="Date of Joining",related="employee_id.joining_date",store=True)
	reporting_manager = fields.Many2one('hr.employee',string="Approver 1",related="employee_id.lone_manager_id",store=True)
	reporting_manager_user_id = fields.Many2one('res.users',string="Approver 1 User Id",related="employee_id.lone_manager_id.user_id",store=True)
	department = fields.Many2one('hr.department',string="Department",related="employee_id.department_id",store=True,track_visibility='onchange')
	location_work_id = fields.Many2one('work.location', string="Work Location",related="employee_id.location_work_id",track_visibility='onchange')
	# state = fields.Selection([('draft','Draft'),('hr_submit','Induction Created'),('acknowledged','Acknowledged by Approver 1'),('reject','Disagreed'),('resubmit','Resubmitted'),('emp_approval','Agreed by Employee'),('done','Completed')],string="Stage",default='draft',track_visibility='onchange')
	state = fields.Selection([('draft','Draft'),('hr_submit','Induction Created'),('emp_approval','Agreed by Employee'),('reject','Disagreed'),('resubmit','Resubmitted'),('acknowledged','Acknowledged by Approver 1'),('done','Completed')],string="Stage",default='draft',track_visibility='onchange')

	induction_line_ids = fields.One2many('hr.induction.line','induction_id',default = _default_induction_line)
	user_id = fields.Many2one('res.users', string='Related User', index=True, track_sequence=2, related="employee_id.user_id",store=True)
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	remarks_by_l1_manager = fields.Text(string="Acknowledgement by Approver 1",track_visibility='onchange',readonly=True)
	remarks_by_employee = fields.Text(string="Reason for Rejection / Disagree",track_visibility='onchange',readonly=True)
	document_created_by = fields.Many2one('res.users',default=lambda self: self.env.uid,string="Hr User Id")
	induction_confirm_date = fields.Datetime(string='Induction Confirmed by HR', track_visibility='onchange', track_sequence=2)
	emp_accept_date = fields.Datetime(string='Employee Agreed', track_visibility='onchange', track_sequence=2)
	emp_rejected_date = fields.Datetime(string='Employee Disagreed', track_visibility='onchange', track_sequence=2)
	hr_resubmit_date = fields.Datetime(string='HR ReSubmitted', track_visibility='onchange', track_sequence=2)
	l1_manager_ack_date = fields.Datetime(string='L1 Manager Acknowledge', track_visibility='onchange', track_sequence=2)
	created_hr_employee_id = fields.Many2one('hr.employee', string="HR")

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
			self.hr_ids = self.created_hr_employee_id

	hr_reminder_approver1_ids = fields.Many2many('hr.employee', string='Noti1 Approver1',
												 compute="compute_employee_approver1_id")
	hr_reminder_approver2_ids = fields.Many2many('hr.employee', string='Noti2 Approver2',
												 compute="compute_employee_approver1_id")
	hr_reminder_hod_ids = fields.Many2many('hr.employee', string='Noti3 Hod',
										   compute="compute_employee_approver1_id")
	hr_reminder_director_ids = fields.Many2many('hr.employee', string='Noti4 Director',
												compute="compute_employee_approver1_id")
	employee_ids = fields.Many2many('hr.employee', string='Noti5 Employee Ids', compute="compute_employee_approver1_id")
	hr_ids = fields.Many2many('hr.employee', string='Noti6 Employee Ids', compute="compute_employee_approver1_id")
	

	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('hr.induction')
		rec = super(HrInduction,self).create(vals)
		return rec

	@api.multi
	def action_hr_confirm(self):
		is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
		for line in self:
			if is_hr:
				line.write({'state':'hr_submit','induction_confirm_date': datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_induction_to_employee')
				template_id.send_mail(self.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'Induction process is completed for you',
					'employee_id': line.employee_id.id, 'model_name': 'hr.induction',
					'approver_ids': [(6, 0, line.employee_ids.ids)],
					'hr_induction_id': line.id
				})
			else:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))


	@api.multi
	def action_emp_reject(self):
		current_employee = self.env.uid
		is_employee = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for line in self:
			if line.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))
			if line.user_id.id == current_employee:
				template_id = self.env.ref('hr_employee_kra.email_template_induction_employee_rejection_to_hr')
				template_id.send_mail(self.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'Employee disagreed Induction Checklist',
					'employee_id': line.employee_id.id, 'model_name': 'hr.induction',
					'approver_ids': [(6, 0, line.hr_ids.ids)],
					'hr_induction_id': line.id
				})

				# line.write({'state':'reject','emp_rejected_date': datetime.now()})
				form_view = self.env.ref('hr_employee_kra.form_induction_emp_reject_remark_wizard')
				return {
		            'name': "Reason for Rejection / Disagree",
		            'view_mode': 'form',
		            'view_type': 'form',
		            'view_id': form_view.id,
		            'res_model': 'induction.emp.reject.remark',
		            'type': 'ir.actions.act_window',
		            'target': 'new',
		            'context': {
		                'induction_id': self.ids, 'is_reject': True
		            },
		            # 'emp_rejected_date': datetime.now()
		        }
			

	@api.multi
	def action_emp_accept(self):
		current_employee = self.env.uid
		is_employee = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for line in self:
			if line.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))
			if line.user_id.id == current_employee:
				var = line.remarks_by_employee
				# print("BBBB", var)
				# line.remarks_by_employee.replace("Disagree", "")
				line.write({'state':'emp_approval','emp_accept_date': datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_induction_employee_confirms_to_a1')
				template_id.send_mail(self.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'Employee had submitted his Induction',
					'employee_id': line.employee_id.id, 'model_name': 'hr.induction',
					'approver_ids': [(6, 0, line.hr_reminder_approver1_ids.ids)],
					'hr_induction_id': line.id
				})
				
	@api.multi
	def action_hr_resubmit(self):
		is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
		for line in self:
			if is_hr:
				line.write({'state':'resubmit','remarks_by_employee':'','hr_resubmit_date': datetime.now()})
			else:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))
			

	@api.multi
	def action_l1_manager_acknowledge(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if line.reporting_manager_user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Acknowledge this document.'))
			if line.reporting_manager_user_id.id == current_employee and is_approver_1:
				# line.write({'state':'acknowledged','l1_manager_ack_date' : datetime.now()})
				form_view = self.env.ref('hr_employee_kra.form_induction_acknowledge_remark_wizard')
				return {
		            'name': "Acknowledgement",
		            'view_mode': 'form',
		            'view_type': 'form',
		            'view_id': form_view.id,
		            'res_model': 'induction.acknowledge.remark',
		            'type': 'ir.actions.act_window',
		            'target': 'new',
		            'context': {
		                'induction_id': self.ids, 'is_acknowledge': True
		            },
		            #'l1_manager_ack_date' : datetime.now()
		        }
			

	@api.multi
	def action_hr_confirm_resubmit(self):
		current_employee = self.env.uid
		is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
		for line in self:
			if is_hr:
				line.write({'state':'hr_submit','hr_resubmit_date': datetime.now()})
			else:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			if self.env['hr.induction'].search([('employee_id', '=', self.employee_id.id)]):
				raise UserError(_('Already Induction Created for this Employee.'))


class HrInductionLine(models.Model):
	_name = 'hr.induction.line'
	# _inherit = ['mail.thread']

	induction_id = fields.Many2one('hr.induction')

	name = fields.Char(string="Particulars")
	session_details = fields.Char(string="Session Details",track_visibility="onchange")
	responsibility = fields.Many2one('hr.department',string="Session Taken by/Responsibility")
	completed = fields.Selection([('completed','Completed'),('pending', 'Pending'), ('na','N/A')],string="Status",track_visibility='onchange')
	user_id = fields.Many2one('User', default=lambda self: self.env.uid)
	is_hr = fields.Boolean('HR', compute='_compute_hr')

	@api.depends('user_id')
	def _compute_hr(self):
		for rec in self:
			var = self.env.user.has_group('hr_employee_kra.group_kra_hr')
			# print("VAR", var)
			if var:
				rec.is_hr = True


