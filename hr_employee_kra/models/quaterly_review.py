from ast import literal_eval
from odoo import api, fields,models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import odoo.addons.decimal_precision as dp
from datetime import datetime
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class KraQuarterly(models.Model):
	_name = 'kra.quarterly'
	_inherit = ['mail.thread']
	_order = 'id desc'

	name = fields.Char('Name')
	state = fields.Selection([('draft', 'Draft'),('app1', 'Submitted by Employee'),('l1_resub', 'PIP Revised by Approver 1'), ('app2', 'Approved by Approver 1'),('reject','Rejected by Approver 2'),  ('done', 'Done'), ('cancel', '')],
							 default='draft', copy=False, string="Stage", track_visibility='onchange')
	employee_id = fields.Many2one('hr.employee', 'Employee', required=True, track_visibility='onchange')
	employee_code = fields.Char('Employee Code', related="employee_id.employee_id")
	job_id = fields.Many2one('employee.designation', string="Designation", related="employee_id.designation_id", readonly=False, track_visibility='onchange')
	seq_date = fields.Datetime(string="Seq Date", default=lambda self: fields.datetime.now(), track_visibility='onchange')
	date = fields.Date('Review Date', store=True, default=lambda self:fields.date.today(), track_visibility='onchange')
	doj = fields.Date('Date of Joining', related="employee_id.joining_date", track_visibility='onchange')
	department_id = fields.Many2one('hr.department', 'Department', related="employee_id.department_id", track_visibility='onchange')
	manager_id = fields.Many2one('hr.employee', 'Manager', related="employee_id.parent_id", track_visibility='onchange')
	location_work_id = fields.Many2one('work.location', string="Work Location",related="employee_id.location_work_id",track_visibility='onchange')
	contract_id = fields.Many2one('hr.contract', 'Contract', track_visibility='onchange')
	kra_id = fields.Many2one('hr.kra', 'KRA Ref No.', readonly=True)
	quarterly_ids = fields.One2many('quarterly.review', 'review_id', 'Quarterly', track_visibility='onchange')
	employee_feedback = fields.Text('Employee Feedback', track_visibility='onchange')
	l1_feedback = fields.Text('Approver 1 Feedback', track_visibility='onchange')
	l2_feedback = fields.Text('Approver 2 Feedback', track_visibility='onchange')
	overall_rating = fields.Float('Overall Rating (%)', compute="compute_total")
	last_quarter_rating = fields.Float('Last Quarter Rating', compute="compute_last_total")
	last_quarter_pip = fields.Text('Last Quarter PIP Details')
	kra_quart_count = fields.Integer( string='# PO', compute="_compute_kra_quart_count")

	l1_manager = fields.Many2one('hr.employee', 'Approver1',related="employee_id.lone_manager_id")
	l2_manager = fields.Many2one('hr.employee', 'Approver2',related="employee_id.ltwo_manager_id")

	user_id = fields.Many2one('res.users', 'User', related="employee_id.user_id")
	l1_manager_id = fields.Many2one('res.users', 'Approver1 id', related="l1_manager.user_id")
	l2_manager_id = fields.Many2one('res.users', 'Approver2 id', related="l2_manager.user_id")
	company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id")
	#company_id has to change based on the employee selected
	approver_1_date = fields.Datetime(string="Approved 1 Date", track_visibility='onchange')
	approver_2_date = fields.Datetime(string="Approved 2 Date", track_visibility='onchange')
	resumbitted_app_2_date = fields.Datetime(string="Resubmitted By L2 For below 70%", track_visibility='onchange')
	revised_emp_date = fields.Datetime(string="Revised By L1 For below 70%", track_visibility='onchange')
	employee_date = fields.Datetime(string="Submitted Date", track_visibility='onchange')
	# submit_approver_1_date = fields.Date(string="Submit to A1", track_visibility='onchange')

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

	@api.multi
	@api.depends('user_id', 'l1_manager_id', 'l2_manager_id')
	def compute_access_rights(self):
		current_employee = self.env.uid
		is_user_group = self.env.user.has_group('hr_employee_kra.group_kra_user')
		is_approver_1_group = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		is_approver_2_group = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for value in self:
			# Employee
			if value.employee_id.user_id.id == current_employee and is_user_group:
				value.is_employee = True
			else:
				value.is_employee = False
			#Approver 1

			if value.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1_group:
				value.is_approver_1 = True
			else:
				value.is_approver_1 = False
			# Approver 2
			if value.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2_group:
				value.is_approver_2 = True
			else:
				value.is_approver_2 = False



	is_employee = fields.Boolean(string="Is Employee", compute='compute_access_rights')
	is_approver_1 = fields.Boolean(string="Is Approver 1", compute='compute_access_rights')
	is_approver_2 = fields.Boolean(string="Is Approver 2", compute='compute_access_rights')

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('kra.quarterly')
		res = super(KraQuarterly, self).create(vals)
		return res

	@api.multi
	@api.depends('quarterly_ids')
	def compute_total(self):
		total = 0
		var = 0
		for val in self:
			for vals in val.quarterly_ids:
				if vals.avg_rating > 0:
					total += vals.avg_rating
					var += len(val)
					val.overall_rating = (total / var) * 10
	@api.multi
	def compute_last_total(self):
		for last in self:
			if last.kra_quart_count:
				quart_search = self.env['kra.quarterly'].search([('state', '=', 'done'), ('employee_id', '=', last.employee_id.id)], order='id desc', limit=1)
				for vals in quart_search:
					last.last_quarter_rating = vals.overall_rating

	@api.multi
	def action_app1(self):
		current_employee = self.env.uid
		is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for lines in self:
			if lines.employee_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Submit this document.'))
			if lines.employee_id.user_id.id == current_employee and is_user:
				lines.write({'state': 'app1', 'employee_date': datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_quarterly_emp_to_a1')
				template_id.sudo().send_mail(lines.id, force_send=True)
				# Reminder Notification
				hr_reminder = lines.env['hr.reminder'].sudo().create({
					'name': 'Employee Submitted Quarterly assessment',
					'employee_id': lines.employee_id.id, 'model_name': 'kra.quarterly',
					'approver_ids': [(6, 0, lines.hr_reminder_approver1_ids.ids)],
					'kra_quarterly_appraisal_id': lines.id
				})

	@api.multi
	def accept_pip_user(self):
		current_employee = self.env.uid
		is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
		for line in self:
			if line.employee_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Resubmit this document.'))
			if line.employee_id.user_id.id == current_employee and is_user:
				line.write({'state': 'done'})

	@api.multi
	def action_app2(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if line.l1_manager_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Resubmit this document.'))
			if line.l1_manager_id.id == current_employee and is_approver_1:
				line.write({'state': 'app2',
				'approver_1_date':datetime.now()})
				template_id = self.env.ref('hr_employee_kra.email_template_quarterly_a1_to_a2')
				template_id.sudo().send_mail(line.id, force_send=True)
				# Reminder Notification
				hr_reminder = line.env['hr.reminder'].sudo().create({
					'name': 'Approver1 Approved Quarterly assessment',
					'employee_id': line.employee_id.lone_manager_id.id, 'model_name': 'kra.quarterly',
					'approver_ids': [(6, 0, line.hr_reminder_approver2_ids.ids)],
					'kra_quarterly_appraisal_id': line.id
				})

	@api.multi
	def action_approve(self):
		current_employee = self.env.uid
		is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for line in self:
			if line.l2_manager_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Resubmit this document.'))
			if line.l2_manager_id.id == current_employee and is_approver_2:
				if line.overall_rating < 70:
					template_id = self.env.ref('hr_employee_kra.email_template_quarterly_approve1')
					template_id.send_mail(line.id, force_send=True)
					line.write({'state': 'reject',
					'resumbitted_app_2_date': datetime.now()})
				else:
					line.write({'state': 'done',
					'approver_2_date':datetime.now()})


	@api.multi
	def state_l2_resub(self):
		current_employee = self.env.uid
		is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		for line in self:
			if line.l1_manager_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Resubmit this document.'))
			if line.l1_manager_id.id == current_employee and is_approver_1:
				line.write({'state': 'l1_resub',
					'revised_emp_date':datetime.now()})


	@api.multi
	def action_cancel(self):
		self.write({'state': 'cancel'})

	@api.multi
	def set_to_draft(self):
		self.write({'state': 'draft'})

	@api.multi
	def action_view_kra_quart(self):
		self.ensure_one()
		action = self.env.ref('hr_employee_kra.action_kra_quarterly').read()[0]
		kra_list = []
		quart_search = self.env['kra.quarterly'].search([('state', '=', 'done'), ('employee_id', '=', self.employee_id.id)], order='id desc', limit=4)
		for count in quart_search:
			kra_list.append(count.id)
		if len(kra_list) >= 1:
			action['domain'] = [('id', 'in', kra_list)]
			return action

	def _compute_kra_quart_count(self):
		for kra in self:
			kra_list = []
			quart_search = self.env['kra.quarterly'].search([('state', '=', 'done'), ('employee_id', '=', self.employee_id.id)], order='id desc', limit=4)
			for count in quart_search:
				kra_list.append(count.id)
			kra.kra_quart_count = len(kra_list)

class QuarterlyReview(models.Model):
	_name = 'quarterly.review'

	review_id = fields.Many2one('kra.quarterly', 'Review')
	state = fields.Selection([('draft', 'Draft'),('app1', 'Submitted by Employee'),('l1_resub', 'PIP Revised by Approver 1'), ('app2', 'Approved by Approver 1'),('reject','Rejected by Approver 2'),  ('done', 'Done'), ('cancel', '')],
							 default='draft', copy=False, string="Stage",related='review_id.state')
	
	kra = fields.Char('KRA')
	details_kra = fields.Char('Details of KRA')
	timeline_id = fields.Many2one('timeline.master', string="Timeline")
	timeline = fields.Selection([('daily', 'Daily'),
								  ('weekly', 'Weekly'),
								  ('monthly', 'Monthly'),
								  ('as&when', 'As & When'),
								  ('annually', 'Annually'),
								  ('quarterly', 'quarterly'),
								  ('regular', 'Regular')],
								  string="Timeline")
	weightage = fields.Char('Weightage')
	max_rating = fields.Float('Max Rating', default=10)
	details_acheivement = fields.Char('Details of Acheivement')
	employee_rating = fields.Integer('Employee Rating')
	l1 = fields.Integer('Approver 1')
	l2 = fields.Integer('Approver 2')
	avg_rating = fields.Float('Average Rating', compute="compute_avg")
	employee_feedback = fields.Text('Employee Feedback')
	l1_feedback = fields.Text('Approver 1 Feedback')
	l2_feedback = fields.Text('Approver 2 Feedback')
	employee_id = fields.Many2one('hr.employee', 'Employee', related='review_id.employee_id')
	l1_manager = fields.Many2one('hr.employee', 'Approver1', related="employee_id.lone_manager_id")
	l2_manager = fields.Many2one('hr.employee', 'Approver2', related="employee_id.ltwo_manager_id")

	@api.multi
	@api.depends('employee_id', 'l1_manager', 'l2_manager')
	def _check_users_access(self):
		current_employee = self.env.uid
		is_user_group = self.env.user.has_group('hr_employee_kra.group_kra_user')
		is_approver_1_group = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
		is_approver_2_group = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
		for value in self:
			# Employee
			if value.employee_id.user_id.id == current_employee and is_user_group:
				value.user_check = True
			else:
				value.user_check = False

			# Approver 1
			if value.l1_manager.user_id.id == current_employee and is_approver_1_group:
				value.approver_1_check = True
			else:
				value.approver_1_check = False
			# Approver 2
			if value.l2_manager.user_id.id == current_employee and is_approver_2_group:
				value.approver_2_check = True
			else:
				value.approver_2_check = False


	user_check = fields.Boolean(string="User Check", compute='_check_users_access')
	approver_1_check = fields.Boolean(string="Approver 1 Check", compute='_check_users_access')
	approver_2_check = fields.Boolean(string="Approver 2 Check", compute='_check_users_access')


	@api.multi
	@api.depends('employee_rating', 'l1', 'l2','max_rating')
	def compute_avg(self):
		for vals in self:
			if vals.employee_rating > vals.max_rating or vals.l1 > vals.max_rating or vals.l2 > vals.max_rating:
				raise ValidationError(_("Rating Should not be Greater than Max Rating..."))
			if vals.employee_rating and vals.l1 and vals.l2:
				avg = 0
				avg = vals.employee_rating + vals.l1 + vals.l2
				vals.avg_rating = avg / 3
			elif vals.employee_rating and vals.l1:
				avg = 0
				avg = vals.employee_rating + vals.l1
				vals.avg_rating = avg / 2
			elif vals.employee_rating and vals.l2:
				avg = 0
				avg = vals.employee_rating + vals.l2
				vals.avg_rating = avg / 2
			elif vals.l1 and vals.l2:
				avg = 0
				avg = vals.l1 + vals.l2
				vals.avg_rating = avg / 2
			elif vals.employee_rating:
				avg = 0
				avg = vals.employee_rating
				vals.avg_rating = avg / 1
			elif vals.l1:
				avg = 0
				avg = vals.l1
				vals.avg_rating = avg / 1
			elif vals.l2:
				avg = 0
				avg = vals.l2
				vals.avg_rating = avg / 1