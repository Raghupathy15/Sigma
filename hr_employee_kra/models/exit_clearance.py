# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
from datetime import datetime

class ExitClearanceMaster(models.Model):
	_name = 'exit.clearance.master'
	_inherit = ['mail.thread']
	_description = "Exit Clearance Master"

	name = fields.Char(string="Name",required=True)
	employee_id = fields.Many2one('hr.employee',string="Employee Name")
	owner = fields.Many2one('hr.department',string="Department")
	active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the induction master without removing it.")
	exit_clearance_master_date = fields.Datetime(string='Exit Clearance Master',default=lambda self: fields.datetime.now(),track_visibility='onchange')

	@api.onchange('employee_id')
	def onchange_mob(self):
		if self.employee_id:
			self.owner = self.employee_id.department_id.id

class ExitClearance(models.Model):
	_name = 'exit.clearance'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_order = 'id desc'

	@api.model
	def _default_clearance_line(self):
		master = self.env['exit.clearance.master']
		vals = []
		master_ids = master.search([])
		for line in master_ids:
			data={}
			data['name'] = line.name
			data['owner'] = line.owner.id
			data['responsible_id'] = line.employee_id.id
			vals.append((0,0,data))
		return vals

	@api.multi
	def compute_default_employee(self):
		master = self.env['exit.clearance.master'].sudo().search([('active','=',True)])
		rec = ''
		for emp_ids in master:
			rec = emp_ids.employee_id
			var2 = rec
			self.depart_employees_ids = rec.ids


	name = fields.Char(string="Doc No.", copy=False, readonly=True)
	state = fields.Selection([('draft', 'Submitted to HR for Approval'), ('submit_hr', 'Submitted To HOD For Approval'), ('submit_hod', 'Submitted To Director For Approval'), ('submit_director', 'Submitted by Director'), ('done', 'Done'), ('cancel', 'Cancel')],
							 default='draft', copy=False, string="Status", readonly=False, track_visibility='onchange', track_sequence=2)
	resignation_id = fields.Many2one('hr.resignation',string="Resignation Ref ID", readonly=True)
	doc_created_date = fields.Datetime(string="Document Date",default=lambda self: fields.datetime.now())
	rev_date = fields.Date(string="Date",readonly=True)
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now(), readonly=True)
	remarks = fields.Text(string="Remarks")
	employee_id = fields.Many2one('hr.employee',string="Employee Name")
	l1_manager_id = fields.Many2one('hr.employee',string="Approver 1",related="employee_id.lone_manager_id")
	l2_manager_id = fields.Many2one('hr.employee',string="Approver 2",related="employee_id.ltwo_manager_id")
	employee_code = fields.Char(string="Employee Id",related="employee_id.employee_id",store=True)
	job_id = fields.Many2one('employee.designation',string="Designation",related="employee_id.designation_id")
	department_id = fields.Many2one('hr.department',string="Department",related="employee_id.department_id")
	location_work_id = fields.Many2one('work.location', string="Work Location",related="employee_id.location_work_id",track_visibility='always')
	clearance_line_ids = fields.One2many('exit.clearance.line','clearance_id',default=_default_clearance_line)
	user_id = fields.Many2one('res.users', string='Related User', compute="compute_user")
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	depart_employees_ids = fields.Many2many('hr.employee',string="Department Employees",compute="compute_default_employee")
	app_releving_date = fields.Date(string="Approved releving Date",readonly=True)

	@api.depends('user_id')
	def compute_user(self):
		for vals in self:
			vals.user_id = vals.env.uid

	@api.multi
	def action_submit(self):
		is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
		for line in self:
			if is_hr:
				line.rev_date = str(datetime.today())
				line.write({'state': 'submit_hr'})
			else:
				raise UserError(_('You are not a authorized user to perform actions in this document.'))

	@api.multi
	def action_approve(self):
		current_employee = self.env.uid
		for line in self:
			if line.employee_id.hod_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to Approve this document.'))
			if line.employee_id.hod_id.user_id.id == current_employee:
				self.write({'state': 'submit_hod'})

	
	@api.multi
	def action_done(self):
		settlement = self.env['final.settlement']
		final_settlement = settlement.create({'doc_date':fields.Date.today(),
											'employee_id':self.employee_id.id,
											'designation_id':self.job_id.id,
											'last_date': self.resignation_id.approved_revealing_date
											})
		self.write({'state': 'done'})

	@api.multi
	def submit_hr(self):
		current_employee = self.env.uid
		for line in self:
			if line.employee_id.parent_id.user_id.id != current_employee:
				raise UserError(_('You are not a authorized user to approve this document.'))
			else:
				self.write({'state': 'submit_director'})


	@api.multi
	def action_reject(self):
		self.write({'state': 'draft'})

	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('exit.clearance')
		rec = super(ExitClearance,self).create(vals)
		return rec

class ExitClearanceLine(models.Model):
	_name = 'exit.clearance.line'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	clearance_id = fields.Many2one('exit.clearance')
	sl_no = fields.Integer(string="Sl. No.",compute="fetch_sl_no")
	employee_id = fields.Many2one('hr.employee',string="Employee Name",related="clearance_id.employee_id",store=True)
	user_id = fields.Many2one('res.users', string='Related User')
	rev_date = fields.Date(string="Date")
	name = fields.Char(string="Description")
	owner = fields.Many2one('hr.department',string="Owner")
	responsible_id = fields.Many2one('hr.employee',string="Responsible")
	applicable = fields.Selection([('yes','Yes'),('no','No')])
	status = fields.Char(string="Remarks")
	is_employee = fields.Boolean('Empoyee user', compute="compute_user")

	@api.depends('user_id')
	def compute_user(self):
		for vals in self:
			if vals.clearance_id.employee_id.user_id.id == vals.clearance_id.env.uid:
				vals.is_employee = True
			else:
				vals.is_employee = False

	def fetch_sl_no(self):
		sl = 0
		if self.ids:
			line_id = self.browse(self.ids[0])
			for line in line_id.clearance_id.clearance_line_ids:
				sl = sl + 1
				line.sl_no = sl

	@api.onchange('user_id', 'applicable')
	def onchange_user(self):
		for vals in self:
			if vals.applicable == 'yes':
				vals.user_id = vals.env.uid
			if vals.applicable == 'no':
				vals.status = 'Remarks no need.'

