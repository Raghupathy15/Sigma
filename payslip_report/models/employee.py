from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class HrEmployee(models.Model):
	_inherit = 'hr.employee'
		
	code = fields.Char('Employee Code')
	pan = fields.Char('PAN')
	pf_acc = fields.Char('PF Acc No')
	pf_uan = fields.Char('PF UAN')
	esic_no = fields.Char('ESIC')

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'
		
	diff = fields.Char('Diff')

	@api.onchange('date_from', 'date_to')
	def onchange_compute_diff(self):
		if self.date_to and self.date_from:
			delta = self.date_to - self.date_from
			self.diff = delta.days+1