# -*- coding: utf-8 -*-
import logging
from odoo import models, api,fields, _
from itertools import groupby
from odoo.exceptions import UserError,ValidationError

class CancelRemarks(models.TransientModel):
	_name = 'cancel.remarks.resignation'
	_description = "Resignation Cancel Remarks"

	name = fields.Text('Cancel Remarks')

	@api.multi
	def action_cancel_remark(self):
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.resignation'].browse(int(active_id))
		rec.write({'cancel_res':self.name,'state':'cancel_req'})
		template_id = rec.env.ref('hr_resignation.email_template_to_employee_cancelled')
		template_id.sudo().send_mail(rec.id, force_send=True)
		# Reminder Notification
		hr_reminder = rec.env['hr.reminder'].sudo().create({
			'name': 'Empoyee has cancelled the resignation request',
			'employee_id': rec.employee_id.id, 'model_name': 'hr.resignation',
			'approver_ids': [(6, 0, rec.hr_reminder_approver1_ids.ids)],
			'hr_resignation_id': rec.id
		})
