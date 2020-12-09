# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class MobileAttendance(models.Model):
	_inherit='hr.attendance'

	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=False,
								  ondelete='cascade', index=True)
	
	
	attendance_type = fields.Selection([
		('rfid', 'RFID'),
		('mobile_app', 'Mobile App'),
		('geo_fence', 'Geo Fence')
	], string='Attendance Type', related='employee_id.attendance_type')
	device_id = fields.Char(string='Device ID')
	mobile_type = fields.Char(string='Mobile Type')

	