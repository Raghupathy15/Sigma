# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime


class InductionAcknowledge(models.TransientModel):
	_name = 'induction.acknowledge.remark'
	_description = 'Induction Acknowledge Wizard'

	name = fields.Text('Remarks')

	@api.multi
	def action_induction_acknowledge_remark(self):
		if self._context.get('is_acknowledge'):
			for induction_id in self.env['hr.induction'].browse(self._context.get('induction_id', False)):
				induction_id.write({'remarks_by_l1_manager': self.name, 'l1_manager_ack_date' : datetime.now(), 'state': 'done'})


class InductionEmployeeReject(models.TransientModel):
	_name = 'induction.emp.reject.remark'
	_description = 'Induction Reject Wizard'

	name = fields.Text('Reason')

	@api.multi
	def action_induction_emp_reject_remark(self):
		if self._context.get('is_reject'):
			for induction_id in self.env['hr.induction'].browse(self._context.get('induction_id', False)):
				induction_id.write({'remarks_by_employee': self.name, 'emp_rejected_date': datetime.now(), 'state': 'reject'})