from odoo import models, fields, api, _
from datetime import datetime


class Partner(models.Model):
	_inherit = "res.partner"

	email = fields.Char()

	@api.one
	@api.onchange('employee')
	def onchange_email(self):
		for rec in self:
			red = rec.email
			ramp = self.user_ids.filtered(lambda x: x.partner_id.id == self.id)
			for rar in ramp:
				var = self.env['hr.employee'].sudo().search([('user_id', '=', ramp.id)])
				print("RAMPT", rar, var)
				for res in var:
					print("AAA", res.work_email)
					blue = res.work_email
					if red != blue:
						print("APT")
						rec.email = res.work_email
