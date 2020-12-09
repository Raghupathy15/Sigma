import base64
import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from datetime import datetime

class HrPayslipLeave(models.Model):
	_name='hr.payslip.leave'

	#establishing the one2many relation between models
	leave_payslip_ids = fields.Many2one('hr.payslip')
	leaves_taken = fields.Float(string="Leaves Taken")
	leave_type_id = fields.Many2one('hr.leave.allocation',string="Leave Type")
	employee_id = fields.Many2one('hr.employee',string="Employee Name",related="leave_payslip_ids.employee_id",store=True)
	name = fields.Many2one('hr.employee',related="employee_id")
	date_from = fields.Date(string="From Date",related="leave_payslip_ids.date_from",store=True)
	date_to = fields.Date(string="To Date",related="leave_payslip_ids.date_to",store=True)
	current_year = fields.Integer(string="Current Year",compute="check_year")

	@api.multi
	@api.depends('date_from')
	def check_year(self):
		for line in self:
			present_year = line.date_from
			line.current_year = present_year.year


	@api.multi
	def unlink(self):
		return super(HrPayslipLeave, self).unlink()