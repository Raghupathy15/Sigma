# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime


class KRARemark(models.TransientModel):
	_name = 'kra.remark'
	_description = 'KRA Remark Wizard'

	name = fields.Text('Remarks')
	employee_id = fields.Many2one('hr.employee',string="Employee Name")
	approver_1_id = fields.Many2one('hr.employee',string="Approver 1")
	approver_2_id = fields.Many2one('hr.employee',string="Approver 2")

	@api.multi
	def action_kra_remark(self):
		if self._context.get('is_reject'):
			for kra_id in self.env['hr.kra'].browse(self._context.get('kra_id', False)):
				kra_id.write({'reason_l2_manager': self.name, 'l2_reject_date': datetime.now(), 'state': 'reject'})
				self.write({'employee_id':kra_id.employee_id.id,'approver_1_id':kra_id.reporting_manager.id,'approver_2_id':kra_id.l2_manager.id})
				template_id = self.env.ref('hr_employee_kra.email_template_rej_kra')
				template_id.sudo().send_mail(self.id,force_send=True)
				# Reminder Notification
				hr_reminder = kra_id.env['hr.reminder'].sudo().create({
					'name': 'KRA is rejected by Approver2',
					'employee_id': kra_id.employee_id.id, 'model_name': 'hr.kra',
					'approver_ids': [(6, 0, kra_id.hr_reminder_approver1_ids.ids)],
					'hr_kra_id': kra_id.id
				})


class KRAEmpRemark(models.TransientModel):
	_name = 'kra.emp.remark'
	_description = 'KRA Employee Remark Wizard'

	name = fields.Text('Remarks')
	employee_id = fields.Many2one('hr.employee',string="Employee Name")
	approver_1_id = fields.Many2one('hr.employee',string="Approver 1")
	approver_2_id = fields.Many2one('hr.employee',string="Approver 2")

	@api.multi
	def action_kra_emp_remark(self):
		if self._context.get('is_reject'):
			for kra_id in self.env['hr.kra'].browse(self._context.get('kra_id', False)):
				kra_id.write({'reason_by_employee':self.name,'emp_rejected_date':datetime.now(),'state':'reject_by_emp'})
				self.write({'employee_id':kra_id.employee_id.id,'approver_1_id':kra_id.reporting_manager.id,'approver_2_id':kra_id.l2_manager.id})
				template_id = self.env.ref('hr_employee_kra.email_template_rej_by_employee')
				template_id.sudo().send_mail(self.id,force_send=True)
				# Reminder Notification
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'KRA is rejected by Employee',
					'employee_id': kra_id.employee_id.id, 'model_name': 'hr.kra',
					'approver_ids': [(6, 0, kra_id.hr_reminder_approver1_ids.ids)],
					'hr_kra_id': kra_id.id
				})