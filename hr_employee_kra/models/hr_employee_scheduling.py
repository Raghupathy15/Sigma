# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError
class HrEmployeeScheduling(models.Model):
	_name = 'hr.employee.scheduling'

	name = fields.Char(string="Particulars")
	date = fields.Date(string="Scheduled Date")
	schedule_id = fields.Many2one('hr.employee','Employee Master Id')

