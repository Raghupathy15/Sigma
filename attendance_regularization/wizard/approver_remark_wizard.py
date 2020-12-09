# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime, date, time, timedelta


class RegularApproverRemark(models.TransientModel):
	_name = 'regular.approver.remark'
	_description = 'Regular Approver Remark Wizard'

	name = fields.Text('Approver Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="regular_id.employee")
	regular_id = fields.Many2one('attendance.regular', 'Regular')

	###### Hr Reminder/Noitification

	@api.depends('employee_id')
	def approver_users(self):
		for vals in self:
			employee_data = self.env['hr.employee'].sudo().search([('id', '=', vals.employee_id.id)])
			for data in employee_data:
				vals.hr_reminder_approver_id = data.id

	hr_reminder_approver_ids = fields.Many2many('hr.employee', string='Notification Approver', compute="approver_users",
												store=True)

	@api.multi
	def action_regular_approver_remark(self):
		if self._context.get('is_reject'):
			for attendance_id in self.env['attendance.regular'].browse(self._context.get('attendance_id', False)):
				attendance_id.write({'approver_remarks': self.name, 'state_select': 'reject'})
				template_id = self.env.ref('attendance_regularization.email_template_reject_attendance_regularized')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Attendance Rgularization Rejected',
					'employee_id': self.employee_id.id,
					'approver_ids': [(6, 0, self.hr_reminder_approver_ids.ids)],
					'attendance_regular_id': self.regular_id.id
				})
				for attn in self.env['hr.attendance'].search([('employee_id','=',attendance_id.employee.id)]):
					if attn.employee_id:
						if attn.check_in:
							if attn.check_in.date() == attendance_id.reg_date:
								if attn.reg_req == True:
									attn.write({'reg_rejected':True,'reg_approved':False})                                