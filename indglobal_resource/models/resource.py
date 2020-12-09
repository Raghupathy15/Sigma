# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models,_
import re
from odoo.exceptions import ValidationError,UserError
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ResourceCalendarLeaves(models.Model):
	_inherit = "resource.calendar.leaves"

	work_location_id = fields.Many2one('work.location', string='Work Location',required=True)

	@api.multi
	def _cron_holiday(self):
		# To create Holiday in attendance
		current_date = fields.Date.today()

		# To create weakoff in attendance
		date_start = current_date - relativedelta(months=2)
		while date_start <= current_date:
			date_start = date_start + relativedelta(days=1)
			if (date_start.strftime("%A") == "Sunday"):
				for employee in self.env['hr.employee'].sudo().search([('active','=',True),('payroll','=','yes')]):
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',date_start),('employee_id','=',employee.id)])
					if not attendance:
						atten = self.env['hr.attendance']
						obj = atten.create({'logged_date': date_start,'employee_id': employee.id,'is_weekoff':True,'week_off':1})
					elif attendance:
						for attn in attendance:
							attn.write({'is_weekoff': True,'week_off': 1})

		for employee in self.env['hr.employee'].sudo().search([('active','=',True),('payroll','=','yes')]):
			for holiday in self.env['resource.calendar.leaves'].sudo().search([('work_location_id','=',employee.location_work_id.id),('company_id','=',employee.company_id.id)]):
				if holiday.work_location_id:
					attendance = self.env['hr.attendance'].sudo().search([('logged_date','=',holiday.date_holiday),('employee_id','=',employee.id)])
					if str(holiday.date_holiday) <= str(current_date):
						if holiday and not attendance:
							atten = self.env['hr.attendance']
							obj = atten.create({'logged_date':holiday.date_holiday,'employee_id': employee.id,'is_holiday':True,'holiday':1})
						elif holiday and attendance:
							for vals in attendance:
								vals.write({'is_holiday':True,'holiday':1})
			attendance_abs = self.env['hr.attendance'].sudo().search([('employee_id','=',employee.id),('logged_date','=',current_date)])
			if not attendance_abs:
				vals = attendance_abs.sudo().create({
											'employee_id':employee.id,
											'logged_date':current_date,
											'is_absent':True
											})
		

