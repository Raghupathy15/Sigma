# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo import api, fields, models, tools, _
from datetime import datetime

class ResUsers(models.Model):
	_inherit = 'res.users'

	is_blocked = fields.Boolean(string='Is Blocked?', default=False)
	blocked_date_mail = fields.Date("Blocked Date")
	blocked_mail = fields.Char("Two days")
	blocked_mail_four_days = fields.Char("Four days")

class HREmployee(models.Model):
	_inherit = 'account.analytic.line'

	# If account is blocked for 2 or 4 days- mail to employee,app,hod
	@api.multi
	def _cron_is_blocked_mail_to_employees(self):
		import datetime
		curr_date = fields.Date.today()
		two_days = curr_date + datetime.timedelta(days=-2)
		four_days = curr_date + datetime.timedelta(days=-4)

		emp = self.env['hr.employee'].search([('active','=',True)])
		for employee in emp:
			mail = employee.lone_manager_id.work_email
			mail_2 = employee.ltwo_manager_id.work_email
			mail_3 = str(mail) + ',' + str(mail_2)
			mail_4 = str(mail_3) +','+ str(employee.hod_id.work_email) + ',' + str(employee.parent_id.work_email)
			employee.blocked_mail = mail_3
			employee.blocked_mail_four_days = mail_4
			# Two days
			if employee.user_id.is_blocked == True and employee.user_id.blocked_date == two_days:
				if employee.id == employee.user_id.employee_id.id:
					template_id = self.env.ref('hr_timesheet_extended.email_template_if_account_emp_v3')
					template_id.sudo().write({'email_to':employee.work_email})
					template_id.sudo().write({'email_cc':employee.blocked_mail})
					template_id.sudo().send_mail(employee.id, force_send=True)
			# Four days
			if employee.user_id.is_blocked == True and employee.user_id.blocked_date == four_days:
				if employee.id == employee.user_id.employee_id.id:
					emplate_id = self.env.ref('hr_timesheet_extended.email_template_if_account_emp_v4')
					template_id.sudo().write({'email_to':employee.work_email})
					template_id.sudo().write({'email_cc':employee.blocked_mail_four_days})
					template_id.sudo().send_mail(employee.id, force_send=True)