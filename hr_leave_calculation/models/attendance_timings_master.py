# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _
from datetime import datetime,date
import dateutil.parser
from dateutil.relativedelta import relativedelta, MO


import datetime
from datetime import date, datetime, time
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT



class HrAttendanceMaster(models.Model):
	_name = 'hr.attendance.master'

	name = fields.Char(string="Code",default="Attendance Timings")
	active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the attendance master configuration without removing it.")
	first_half_login_early = fields.Char(string="Login from")
	first_half_login_early_two = fields.Char(string="Login to")
	second_half_login = fields.Char(string="Login")
	min_hours_to_work = fields.Char(string="Minimum Hours to work")
	total_hours_to_work = fields.Char(string="Total Hours to work")
	# check_bool = fields.Boolean(string="Boolean", compute="convert_to_seconds")
	# check_field = fields.Char(string="Check", compute="convert_to_seconds")

	# @api.multi
	# @api.depends('first_half_login_early','first_half_login_early_two','second_half_login','min_hours_to_work','total_hours_to_work')
	# def convert_to_seconds(self):
	# 	early_str = early_hour = early_min = 0.00
	# 	for line in self:
	# 		early_str = str(line.first_half_login_early)
	# 		early_hour,early_min = early_str.split(':')
	# 		line.check_field = float(early_hour)* 3600 + float(early_min) *60
	# 		# line.check_field = str(line.first_half_login_early)

	