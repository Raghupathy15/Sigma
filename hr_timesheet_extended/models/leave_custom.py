# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class Holidays(models.Model):
	_inherit = "hr.leave"

	def _validate_leave_request(self):
		""" Timesheet will be generated on leave validation only if a timesheet_project_id and a
			timesheet_task_id are set on the corresponding leave type. The generated timesheet will
			be attached to this project/task.
		"""
		# create the timesheet on the vacation project
		for holiday in self.filtered(
				lambda request: request.holiday_type == 'employee' and
								request.holiday_status_id.timesheet_project_id and
								request.holiday_status_id.timesheet_task_id):
			holiday_project = holiday.holiday_status_id.timesheet_project_id
			holiday_task = holiday.holiday_status_id.timesheet_task_id

			work_hours_data = holiday.employee_id.list_work_time_per_day(
				fields.Datetime.from_string(holiday.date_from),
				fields.Datetime.from_string(holiday.date_to),
			)
			# for index, (day_date, work_hours_count) in enumerate(work_hours_data):
			# 	if holiday.state == 'validate' or holiday.state == 'validate1':
			# 		self.env['account.analytic.line'].create({
			# 			'name': "%s (%s/%s)" % (holiday.name or '', index + 1, len(work_hours_data)),
			# 			'project_id': holiday_project.id,
			# 			'task_id': holiday_task.id,
			# 			'account_id': holiday_project.analytic_account_id.id,
			# 			'unit_amount': work_hours_count,
			# 			'user_id': holiday.employee_id.user_id.id,
			# 			'date': fields.Date.to_string(day_date),
			# 			'holiday_id': holiday.id,
			# 			'employee_id': holiday.employee_id.id,
			# 			'state': 'approved'
			# 		})

		return super(Holidays, self)._validate_leave_request()
