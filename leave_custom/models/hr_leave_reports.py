# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class LeaveReport(models.Model):
	_inherit = "hr.leave.report"

	# days_display = fields.Float('Number of Days display')

	# @api.constrains('number_of_days')
	# def _check_no_of_days(self):
	# 	name_rec = self.env['hr.leave.report'].search([])
	# 	print ('==============',name_rec)
	# 	for rec in name_rec:
	# 		# if not rec.state in ('cancel','refuse'):
	# 		if rec.number_of_days < 0:
	# 			print ('$$$$$$$$$$$$$$$$$$$$$',rec.number_of_days)
	# 			print ('$$$$$$$$$$$$$$$$$$$$$',abs(rec.number_of_days))
	# 			rec.number_of_days = abs(rec.number_of_days)


