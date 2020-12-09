# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

class Applicant(models.Model):
	_inherit = 'hr.applicant'
	#renaming of fields
	salary_proposed = fields.Float("Proposed CTC", group_operator="avg", help="Salary Proposed by the Organisation")
	salary_expected = fields.Float("Expected CTC", group_operator="avg", help="Salary Expected by Applicant")