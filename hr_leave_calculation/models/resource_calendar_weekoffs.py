import base64
import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from datetime import datetime


class ResourceCalendar(models.Model):
	_inherit = 'resource.calendar'

	weekoffs_ids = fields.One2many('resource.calendar.weekoffs','weekoffs_id')

class ResourceCalendarLeaves(models.Model):
	_inherit = 'resource.calendar.leaves'

	from_date = fields.Date(string="Date from", compute="fetch_date")
	to_date = fields.Date(string="Date To", compute="fetch_date")
	days_count = fields.Float(string="Days Count",compute="fetch_date")

	@api.multi
	@api.depends('date_from','date_to')
	def fetch_date(self):
		delta = 0
		for line in self:
			if line.date_from and line.date_to:
				date_from_time = fields.Datetime.from_string(line.date_from)
				date_to_time = fields.Datetime.from_string(line.date_to)

				date_from_without_time = str(date_from_time)
				date_to_without_time = str(date_to_time)

				line.from_date = date_from_without_time[:10]
				line.to_date = date_to_without_time[:10]

				if line.to_date >= line.from_date:
					delta = line.to_date - line.from_date
					line.days_count = delta.days + 1
				



class ResourceCalendarWeekoffs(models.Model):
	_name='resource.calendar.weekoffs'
	_order = 'weekoff_date'

	name = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of WeekOff', required=True, index=True, default='0')
	weekoff_date = fields.Date(string="Date")
	weekoffs_id = fields.Many2one('resource.calendar',string="Resource Calendar")

