# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class HolidaysAllocation(models.Model):
	_inherit = "hr.leave.allocation"

	el_sl_date = fields.Date(string="EL & SL Date")
	pl_date = fields.Date(string="PL Date")

	# active=fields.boolean('Active')
	company_id = fields.Many2one('res.company',string="Company",related='employee_id.company_id',store=True)
	def activity_update(self):
		to_clean, to_do = self.env['hr.leave.allocation'], self.env['hr.leave.allocation']
		for allocation in self:
			if allocation.state == 'draft':
				to_clean |= allocation
			# elif allocation.state == 'confirm':
				# allocation.activity_schedule(
				# 	# 'hr_holidays.mail_act_leave_allocation_approval',
				# 	user_id=allocation.sudo(). self.env.user.id)
			# elif allocation.state == 'validate1':
				# allocation.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval'])
				# allocation.activity_schedule(
				# 	# 'hr_holidays.mail_act_leave_allocation_second_approval',
				# 	user_id=allocation.sudo(). self.env.user.id)
			elif allocation.state == 'validate':
				to_do |= allocation
			elif allocation.state == 'refuse':
				to_clean |= allocation
		# if to_clean:
		#     to_clean.activity_unlink(['hr_holidays.mail_act_leave_allocation_approval', 'hr_holidays.mail_act_leave_allocation_second_approval'])
		# if to_do:
		#     to_do.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval', 'hr_holidays.mail_act_leave_allocation_second_approval'])

	


