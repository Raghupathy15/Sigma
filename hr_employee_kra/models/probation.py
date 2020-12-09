from odoo import api, fields,models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class KraProbationMaster(models.Model):
	_name = 'kra.probation.master'
	_inherit = ['mail.thread']
	_description = "Probation Master"

	name = fields.Char('Name',required=True)
	probation_master_created_date = fields.Datetime(string="Probation Master Created",default=lambda self: fields.datetime.now(),track_visibility='onchange')

class KraProbation(models.Model):
	_name = 'kra.probation'
	_inherit = ['mail.thread']
	_order = 'id desc'

	@api.model
	def _default_probation_line(self):
		terms_obj = self.env['kra.probation.master']
		terms = []
		termsids = terms_obj.search([])
		for rec in termsids:
			values = {}
			values['name'] = rec.name
			terms.append((0, 0, values))
		return terms

	name = fields.Char('Name')
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now())
	state = fields.Selection([('draft', 'Draft'), ('hod', 'HOD'),('reject','Rejected by HOD'), ('resubmit', 'Resubmitted'),('extended', 'Probation Extended'),('done', 'Done'),('cancel', 'Cancel')],
							 default='draft', track_visibility='onchange', copy=False, string="Status", readonly=False)
	employee_code = fields.Char('Employee ID', related="employee_id.employee_id", required=True, readonly=False)
	employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=False)
	doc_no = fields.Char('Doc No')
	rev_no = fields.Char('Rev No')
	rev_date = fields.Date('Rev Date')
	ref = fields.Char('Ref')
	contract_id = fields.Many2one('hr.contract', 'Contract')
	department_id = fields.Many2one('hr.department', 'Department', related="employee_id.department_id", required=True, readonly=False)
	designation_id = fields.Many2one('employee.designation', 'Designation', related="employee_id.designation_id", readonly=False)
	hod_id = fields.Many2one('hr.employee', 'HOD', related="employee_id.hod_id", required=True, readonly=False)
	approver1_id = fields.Many2one('hr.employee', 'Approver 1', related="employee_id.lone_manager_id", required=True, readonly=False)
	doj = fields.Date('Date of Joining', related="employee_id.joining_date", required=True, readonly=False)
	prob_date = fields.Date('Date of Probation', required=True, related="employee_id.probation_eval_date")
	review_ids = fields.One2many('employee.review', 'probation_id', default=_default_probation_line)
	is_approver1 = fields.Boolean('Approver 1 user', compute="compute_user")
	is_hod = fields.Boolean('HOD user', compute="compute_user")

	# efficiency = fields.Selection([('improvement', 'Improvement Required'), ('satisfactory', 'Satisfactory'), ('good', 'Good'), ('excellent', 'Excellent')],
	# 						copy=False, string="Work efficiency")
	# attendance = fields.Selection([('improvement', 'Improvement Required'), ('satisfactory', 'Satisfactory'), ('good', 'Good'), ('excellent', 'Excellent')],
	# 						copy=False, string="Attendance")
	# timemanagement = fields.Selection([('improvement', 'Improvement Required'), ('satisfactory', 'Satisfactory'), ('good', 'Good'), ('excellent', 'Excellent')],
	# 						copy=False, string="Time Management")
	# competency = fields.Selection([('improvement', 'Improvement Required'), ('satisfactory', 'Satisfactory'), ('good', 'Good'), ('excellent', 'Excellent')],
	# 						copy=False, string="Competency in the role")
	company_id = fields.Many2one('res.company', 'Company', related='employee_id.company_id', store=True)
	area_performance = fields.Text('If any areas of performance, conduct or attendance require improvement please provide details below')
	employee_service = fields.Text('Where concerns have been identified, please summarise how these will be addressed during further period of employee survice in the company')
	identify_period = fields.Selection([('yes', 'Yes'), ('no', 'No')],
		string='Objectives identified')
	employee_performance = fields.Text("Summarise the employee's performance")
	performance_text = fields.Char("Objectives Reason")
	training_development = fields.Selection([('yes', 'Yes'), ('no', 'No')],
		string='Have the training / development')
	training_text = fields.Char("Development Reason")
	employee_appointment = fields.Selection([('yes', 'Yes'), ('no', 'No')],
		string="Appointment confirmed")
	reason_appointment = fields.Char("Appointment Reason")
	employee_probation_extend = fields.Selection([('yes', 'Yes'), ('no', 'No')],default='no',string="Probation extended")
	reason_probation_extend = fields.Text("Extended Reason")
	hod_remarks = fields.Text("HOD Remarks")
	hod_status = fields.Selection([('approve', 'HOD Approved'), ('reject', 'HOD Rejected')])
	apprver1_remarks = fields.Text("Approver 1 Remarks")
	director_remarks = fields.Text("Director Remarks")
	length_extension = fields.Char('Length Extension')
	new_prob_date = fields.Date('New Probation Date',track_visibility='onchange')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
	#prob_confirm_date = fields.Datetime('Probation confirmed',track_visibility='onchange')
	l1_manager_ack_date = fields.Datetime(string='L1 Submit Date', track_visibility='onchange', track_sequence=2)
	hod_date = fields.Datetime(string="HOD Date", track_visibility='onchange', track_sequence=2)
	is_respective_a1 = fields.Boolean('Respective A1', compute="compute_user")


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

	def compute_user(self):
		for vals in self:
			approver1_group = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
			hod_group = self.env.user.has_group('hr_employee_kra.group_kra_hod')
			if self.employee_id.lone_manager_id.user_id.id == self.env.uid:
				self.is_respective_a1 = True
			else:
				self.is_respective_a1 = False
			for app1 in vals:
				if approver1_group == True:
					app1.is_approver1 = True
			for hod in vals:
				if hod_group == True:
					hod.is_hod = True

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('kra.probation')
		res = super(KraProbation, self).create(vals)
		return res

	@api.multi
	def action_submit(self):
		for vals in self:
			if vals.state == 'reject':
				self.write({'state': 'resubmit'})
			else:
				if vals.identify_period == 'no':
					if not vals.performance_text:
						raise ValidationError(_('You must give Objectives Reason.'))
				if vals.employee_appointment == 'no':
					if not vals.reason_appointment:
						raise ValidationError(_('You must give Appointment Reason.'))
				if vals.training_development == 'no':
					if not vals.training_text:
						raise ValidationError(_('You must give Development Reason.'))
				if vals.employee_probation_extend == 'yes':
					if not vals.reason_probation_extend or not vals.new_prob_date or not vals.length_extension:
						raise ValidationError(_('You must give Extended Reason, New Probation Date and Length Extension.'))
				if not vals.apprver1_remarks:
					raise ValidationError(_('You must give Approver 1 Remarks.'))
			self.write({'state': 'hod', 'l1_manager_ack_date': datetime.now()})
			template_id = self.env.ref('hr_employee_kra.email_template_probation_creation_hod')
			template_id.send_mail(self.id, force_send=True)
			# Reminder Notification
			hr_reminder = vals.env['hr.reminder'].sudo().create({
				'name': 'Probation Evaluation form is created for for Employee',
				'employee_id': vals.employee_id.id, 'model_name': 'kra.probation',
				'approver_ids': [(6, 0, vals.hr_reminder_hod_ids.ids)],
				'hr_probation_id': vals.id
			})
			
	@api.multi
	def action_approve(self):
		current_employee = self.env.uid
		for line in self:
			if line.employee_id.hod_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Accept this document.'))
			if line.employee_id.hod_id.user_id.id == current_employee:
				if line.employee_id:
					for employee in line.employee_id:
						if line.employee_probation_extend == 'no':
							employee.write({'employment_status' : 'confirmed', 'emp_confirmation_date': datetime.now()})
							line.write({'hod_status': 'approve'})
							line.write({'state': 'done'})
							template_id = self.env.ref('cron_probation.email_template_probation_creation_app')
							template_id.send_mail(self.id, force_send=True)
							# Reminder Notification
							hr_reminder = line.env['hr.reminder'].sudo().create({
								'name': 'The Probation Evaluation Process is completed',
								'employee_id': line.employee_id.id, 'model_name': 'kra.probation',
								'approver_ids': [(6, 0, line.employee_ids.ids)],
								'hr_probation_id': line.id
							})
						if line.employee_probation_extend =='yes':
							employee.write({'probation_eval_date1':line.new_prob_date})
							line.write({'hod_status': 'approve'})
							line.write({'state': 'extended', 'hod_date': datetime.now()})
	@api.multi
	def action_reject(self):
		current_employee = self.env.uid
		is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
		for line in self:
			if line.employee_id.hod_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Reject this document.'))
			if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
				form_view = self.env.ref('hr_employee_kra.form_hod_reject_wizard')
				return {
					'name': "Rejection Remarks",
					'view_mode': 'form',
					'view_type': 'form',
					'view_id': form_view.id,
					'res_model': 'probation.reject.wizard',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'context': {
						'probation_id': self.ids,
					}
				}




	@api.multi
	def action_cancel(self):
		self.write({'state': 'cancel'})
	@api.multi
	def set_to_draft(self):
		self.write({'state': 'draft'})

	@api.constrains('new_prob_date')
	def _check_new_prob_date(self):
		for line in self:
			if line.employee_probation_extend == 'yes':
				if line.prob_date:
					# var = DATE(YEAR(joining_date), (MONTH(joining_date)+6),DAY(joining_date))
					var = line.prob_date + relativedelta(days=-1, months=3)
					# print("AAA", var)
					if line.new_prob_date >= var:
						raise ValidationError("New Probation Date Maximum 3 months from the current probation date")
					var_1 = fields.date.today()
					if var_1 >= line.new_prob_date:
						raise ValidationError("New Probation Date Maximum 3 months from the current probation date")


class EmployeeReview(models.Model):
	_name = 'employee.review'

	name = fields.Char('Name')
	# improvement = fields.Boolean('Improvement Required', readonly=False)
	# satisfactory = fields.Boolean('Satisfactory', readonly=False)
	# good = fields.Boolean('Good', readonly=False)
	# excellent = fields.Boolean('Excellent', readonly=False)
	probation_id = fields.Many2one('kra.probation', string='Review')
	quality = fields.Selection([('improvement', 'Improvement Required'), ('satisfactory', 'Satisfactory'), ('good', 'Good'), ('excellent', 'Excellent')],
							copy=False, string="Quality and Accuracy of work")
	state = fields.Selection([('draft', 'Draft'), ('hod', 'HOD'), ('done', 'Done'),('reject','Rejected'), ('cancel', 'Cancel')],
							 default='draft', track_visibility='onchange', copy=False, string="Status",related="probation_id.state")

	# @api.multi
	# @api.onchange('satisfactory','good','excellent')
	# def compute_improvement(self):
	# 	for employee in self:
	# 		if employee.improvement == True:
	# 			if employee.satisfactory == True:
	# 				employee.improvement = False
	# 			elif employee.good == True:
	# 				employee.improvement = False
	# 			elif employee.excellent == True:
	# 				employee.improvement = False
	# # @api.multi
	# @api.onchange('improvement','good','excellent')
	# def compute_satisfactory(self):
	# 	for employee in self:
	# 		if employee.satisfactory == True:
	# 			if employee.improvement == True:
	# 				employee.satisfactory = False
	# 			elif employee.good == True:
	# 				employee.satisfactory = False
	# 			elif employee.excellent == True:
	# 				employee.satisfactory = False
	# # @api.multi
	# @api.onchange('improvement','satisfactory','excellent')
	# def compute_good(self):
	# 	for employee in self:
	# 		if employee.good == True:
	# 			if employee.improvement == True:
	# 				employee.good = False
	# 			elif employee.satisfactory == True:
	# 				employee.good = False
	# 			elif employee.excellent == True:
	# 				employee.good = False
	# # @api.multi
	# @api.onchange('improvement','satisfactory','good')
	# def compute_excellent(self):
	# 	for employee in self:
	# 		if employee.excellent == True:
	# 			if employee.improvement == True:
	# 				employee.excellent = False
	# 			elif employee.satisfactory == True:
	# 				employee.excellent = False
	# 			elif employee.good == True:
	# 				employee.excellent = False


