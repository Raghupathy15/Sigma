# -*- coding: utf-8 -*-
from odoo import fields, models, api

class QuarterlyApprover2Reject(models.TransientModel):
	_name = 'quarterly.approver2.reject.remark'
	_description = 'Quarterly Approver2 Reject Wizard'

	name = fields.Text('Reason')

	@api.multi
	def action_quarterly_approver2_reject_remark(self):
		if self._context.get('is_reject'):
			for quarterly_id in self.env['kra.quarterly'].browse(self._context.get('quarterly_id', False)):
				quarterly_id.write({'l2_feedback': self.name, 'state': 'reject'})