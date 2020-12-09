# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CancelLeaveWizard(models.TransientModel):
	_name = 'cancel.leave.wizard'
	_description = 'Cancel Leave Wizard'

	name = fields.Text('Comment by Approver')
	hr_leave_id = fields.Many2one('hr.leave', 'Leave')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="hr_leave_id.employee_id")

	@api.multi
	def action_cancel_leave(self):
		leave_id = self.env['hr.leave'].browse(self._context.get('leave_id', False))
		leave_id.write({'report_note': self.name, 'state': 'cancel'})
		template_id = self.env.ref('leave_custom.email_template_leave_cancel')
		template_id.sudo().send_mail(leave_id.id, force_send=True)
		hr_reminder = self.env['hr.reminder'].sudo().create({
			'name': 'Your Leave Has Been Cancelled',
			'employee_id': self.employee_id.id, 'model_name': 'hr.leave',
			'approver_ids': [(6, 0, self.hr_leave_id.employee_ids.ids)],
			'hr_leave_id': self.hr_leave_id.id
		})
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.leave'].browse(int(active_id))
		# To unlink the record in attendance
		for attendance in self.env['hr.attendance'].sudo().search([('employee_id','=',rec.employee_id.id),('leave_id','=',rec.id)]):
			if not attendance.check_in and not attendance.check_out:
				attendance.unlink()
			else:
				attendance.write({'leave_days_onch':0,'is_leave':False})				

class RejectLeaveWizard(models.TransientModel):
	_name = 'reject.leave.wizard'
	_description = 'Reject Leave Wizard'

	name = fields.Text('Comment by Approver')
	hr_leave_id = fields.Many2one('hr.leave', 'Leave')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="hr_leave_id.employee_id")

	@api.multi
	def action_reject_leave(self):
		leave_id = self.env['hr.leave'].browse(self._context.get('leave_id', False))
		leave_id.write({'report_note': self.name, 'state': 'refuse'})
		template_id = self.env.ref('leave_custom.email_template_leave_rejected')
		template_id.sudo().send_mail(leave_id.id, force_send=True)
		hr_reminder = self.env['hr.reminder'].sudo().create({
			'name': 'Your Leave Has Been Rejected',
			'employee_id': self.employee_id.id, 'model_name': 'hr.leave',
			'approver_ids': [(6, 0, self.hr_leave_id.employee_ids.ids)],
			'hr_leave_id': self.hr_leave_id.id
		})

