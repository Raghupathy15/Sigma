# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError

class HrContract(models.Model):
	_inherit = 'hr.contract'

	struct_id = fields.Many2one('hr.payroll.structure', string='Grade',compute="fetch_salary_structure",readonly=False,track_visibility='onchange')
	wage = fields.Monetary('GROSS', digits=(16, 2), required=True, track_visibility="onchange", help="Employee's monthly gross wage.")

	@api.multi
	@api.depends('employee_id')
	def fetch_salary_structure(self):
		for line in self:
			struct_id = self.env['hr.payroll.structure'].search([('name','=',line.employee_id.employee_grade_id.name)])
			if struct_id:
				for struct in struct_id:
					line.struct_id = struct.id

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	@api.multi
	def name_get(self):
		result = []
		for line in self:
			name = str(line.employee_id) + ' - ' + line.name
			result.append((line.id, name))
		return result

	applicant_id = fields.Many2one('hr.applicant','Application No.',readonly=True)
	#new fields start
	employee_grade_id = fields.Many2one('employee.grade',string='Grade', required=False,track_visibility='onchange')
	struct_id = fields.Many2one('hr.payroll.structure', string='Grade',readonly=False)
	#new field end
	country_id = fields.Many2one(
        'res.country', 'Nation', groups="hr.group_hr_user")

	induction_ids = fields.One2many('hr.induction', 'employee_id', string='Induction', readonly=True)
	induction_count = fields.Integer(compute='_compute_induction_count', string='Induction Count', groups="hr_employee_kra.group_kra_user")

	probation_ids = fields.One2many('kra.probation', 'employee_id', string='Probation', readonly=True)
	probation_count = fields.Integer(compute='_compute_probation_count', string='Probation Count', groups="hr_employee_kra.group_kra_user")

	quarterly_ids = fields.One2many('kra.quarterly', 'employee_id', string='Quarterly', readonly=True)
	quarterly_count = fields.Integer(compute='_compute_quarterly_count', string='Quarterly Count', groups="hr_employee_kra.group_kra_user")

	appraisal_ids = fields.One2many('kra.appraisal', 'employee_id', string='Appraisal', readonly=True)
	appraisal_count = fields.Integer(compute='_compute_appraisal_count', string='Appraisal Count', groups="hr_employee_kra.group_kra_user")

	kra_ids = fields.One2many('hr.kra', 'employee_id', string='Kra', readonly=True)
	kra_count = fields.Integer(compute='_compute_kra_count', string='KRA Count', groups="hr_employee_kra.group_kra_user")

	@api.multi
	def _compute_induction_count(self):
		for employee in self:
			employee.induction_count = len(employee.induction_ids)

	@api.multi
	def _compute_probation_count(self):
		for employee in self:
			employee.probation_count = len(employee.probation_ids)

	@api.multi
	def _compute_quarterly_count(self):
		for employee in self:
			employee.quarterly_count = len(employee.quarterly_ids)

	@api.multi
	def _compute_appraisal_count(self):
		for employee in self:
			employee.appraisal_count = len(employee.appraisal_ids)

	@api.multi
	def _compute_kra_count(self):
		for employee in self:
			employee.kra_count = len(employee.kra_ids)
	# schedule_ids = fields.One2many('hr.employee.scheduling','schedule_id')


# class HrApplicant(models.Model):
# 	_inherit = 'hr.applicant'

# 	employee_id = fields.Char(string="Employee Id")

# 	@api.multi
# 	def name_get(self):
# 		result = []
# 		for line in self:
# 			name = str(line.sequence_no) + ' - ' + line.name
# 			result.append((line.id, name))
# 		return result

# 	@api.multi
# 	def create_employee_from_applicant(self):
# 		employee = False
# 		grade = 0
# 		for applicant in self:
# 			contact_name = False
# 			#new field
# 			grade_id = self.env['employee.grade'].search([('name','=',applicant.structure_id.name)])
# 			if grade_id:
# 				for grade in grade_id:
# 					grade =  grade_id.id
# 			if applicant.partner_id:
# 				address_id = applicant.partner_id.address_get(['contact'])['contact']
# 				contact_name = applicant.partner_id.name_get()[0][1]
# 			else :
# 				new_partner_id = self.env['res.partner'].create({
# 					'is_company': False,
# 					'name': applicant.name,
# 					'email': applicant.email_from,
# 					'phone': applicant.partner_phone,
# 					'mobile': applicant.partner_mobile
# 				})
# 				address_id = new_partner_id.address_get(['contact'])['contact']
# 			if applicant.job_id and (applicant.name or contact_name) and applicant.employee_id:
# 				applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
# 				employee = self.env['hr.employee'].create({
# 					'name': applicant.name,
# 					'is_hr':True,
# 					'employee_grade_id':grade,
# 					'applicant_id':applicant.id,
# 					'job_id': applicant.job_id.id,
# 					# 'designation_id':applicant.job_id.id,
# 					'address_home_id': address_id,
# 					'employee_id':applicant.employee_id,
# 					'contact_no':applicant.partner_mobile,
# 					'employee_email':applicant.email_from,
# 					'department_id': applicant.department_id.id or False,
# 					'address_id': applicant.company_id and applicant.company_id.partner_id
# 							and applicant.company_id.partner_id.id or False,
# 					'work_email': applicant.department_id and applicant.department_id.company_id
#                             and applicant.department_id.company_id.email or False,
# 					'work_phone': applicant.department_id and applicant.department_id.company_id
# 							and applicant.department_id.company_id.phone or False})
# 				applicant.write({'emp_id': employee.id})
# 				#creating contract
# 				contract = self.env['hr.contract'].create({
# 					'name': applicant.employee_id + ' - '+ applicant.name +' - '+ 'contract',
# 					# 'struct_id':
# 					'wage':applicant.gross_salary,
# 					'mobile_conveyance':applicant.mobile_conveyance,
# 					'city_allowance':applicant.city_allowance,
# 					'employee_id':applicant.emp_id.id,
# 					'state':'open',
# 					'department_id':applicant.department_id.id,
# 					'job_id':applicant.job_id.id,
# 					})
# 				applicant.job_id.message_post(
# 					body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
# 					subtype="hr_recruitment.mt_job_applicant_hired")
# 			else:
# 				raise UserError(_('You must define Employee ID for this applicant.'))
# 			applicant.count_id = 9

# 		employee_action = self.env.ref('hr.open_view_employee_list')
# 		dict_act_window = employee_action.read([])[0]
# 		dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
# 		dict_act_window['res_id'] = employee.id
# 		return dict_act_window