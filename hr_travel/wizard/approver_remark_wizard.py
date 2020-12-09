# -*- coding: utf-8 -*-
from odoo import fields, models, api

# Travel Claim Approver 1 Remark

class ClaimApproverRemark(models.TransientModel):
	_name = 'claim.request.remark'
	_description = 'Travel Approver Remark Wizard'

	name = fields.Text('Approver 1 Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.claim', 'Travel')



	@api.multi
	def action_claim_approver_remark(self):
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.claim'].browse(self._context.get('travel_id', False)):
				travel_id.write({'app1_remarks': self.name, 'state': 'rejected'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_claim_rejection_app1')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Rejected by Approver1',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_claim_id': self.travel_id.id
				})


# Travel Claim HOD Remark

class ClaimRemark(models.TransientModel):
	_name = 'travel.request.remark'
	_description = 'Travel Approver Remark Wizard'

	name = fields.Text('HOD Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.claim', 'Travel')


	@api.multi
	def action_travel_approver_remark(self):
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.claim'].browse(self._context.get('travel_id', False)):
				travel_id.write({'hod_remarks': self.name, 'state': 'rejected'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_claim_rejection_hod')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Rejected by HOD',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_claim_id': self.travel_id.id
				})

# Travel Claim Director Remarks

class ClaimDirectorRemark(models.TransientModel):
	_name = 'travel.claim.director.remark'
	_description = 'Travel Director Remark Wizard'

	name = fields.Text('Director Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.claim', 'Travel')


	@api.multi
	def action_travel_director_remark(self):
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.claim'].browse(self._context.get('travel_id', False)):
				travel_id.write({'dir_remarks': self.name, 'state': 'rejected'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_claim_rejection_director')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Rejected by Director',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_claim_id': self.travel_id.id
				})

# Travel Claim Accounts Remark

class ClaimAccountsRemark(models.TransientModel):
	_name = 'travel.request.remark2'
	_description = 'Travel Request Approver2 Remark'

	def _get_employee_id(self):
		employee_rec = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	name = fields.Text('Accounts Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.claim', 'Travel')
	reject_employee_id = fields.Many2one('hr.employee', default=_get_employee_id, string='Rejected by')

	@api.multi
	def action_travel_approver2_remark(self):
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.claim'].browse(self._context.get('travel_id', False)):
				travel_id.write({'accounts_remarks': self.name, 'state': 'rejected'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_claim_rejection_acc')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Rejected by Accounts',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_claim_id': self.travel_id.id
				})

# Travel Claim HOD Remark

class AdminAccHeadRemark(models.TransientModel):
	_name = 'travel.accounts.head.remark'
	_description = 'Travel Claim Accounts Head Remark'

	def _get_employee_id(self):
		employee_rec = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id
	
	name = fields.Text('Accounts Head Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.claim', 'Travel')
	reject_employee_id = fields.Many2one('hr.employee', default=_get_employee_id, string='Rejected by')

	@api.multi
	def action_travel_acc_head_remark(self):
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.claim'].browse(self._context.get('travel_id', False)):
				travel_id.write({'acc_head_remarks': self.name, 'state': 'rejected'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_claim_rejection_acc_head')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Claim Rejected by Accounts Head',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.claim',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_claim_id': self.travel_id.id
				})

# Travel Admin Approver 1 Remark

class TraveladminApprover1Remark(models.TransientModel):
	_name = 'travel.admin.app1.remark'
	_description = 'Travel Admin Remark Wizard'

	name = fields.Text('Approver 1 Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_admin_approver1_remark(self):
		# To get Active id
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.travel.admin'].browse(int(active_id))
		if rec.is_extend == True or rec.is_add_advance == True or rec.is_return_trip == True:
			rec.additional_advance = 'no'
			rec.days_extension = 0
			rec.is_extend = False
			rec.travel_extend = 'no'
			rec.additional_advance_amount = 0
			rec.is_add_advance = False
			rec.return_ticket = 'no'
			rec.return_date = False
			rec.is_return_ticket = False
			rec.is_return_trip = False
			rec.app1_remarks = self.name
			rec.state = 'travelling'
			# Email - Raghu (STARTS)
			template_id = self.env.ref('hr_travel.email_template_app1_tr_reject')
			template_id.sudo().send_mail(self.id, force_send=True)
			# Email - Raghu (ENDS)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request Rejected by Approver1',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
				'hr_travel_admin_id': self.travel_id.id
			})


		elif self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				if travel_id.booking_status == 'pending':
					travel_id.write({'app1_remarks': self.name, 'state': 'cancelled'})
				elif travel_id.booking_status == 'booked':
					travel_id.write({'app1_remarks': self.name, 'state': 'travelling'})
				# travel_id.write({'app1_remarks': self.name, 'state': 'cancelled'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_app1_tr_reject')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Rejected by Approver1',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})



# Travel Admin Approver 2 Remark

class TraveladminApprover2Remark(models.TransientModel):
	_name = 'travel.admin.app2.remark'
	_description = 'Travel Admin Remark Wizard'

	name = fields.Text('Approver 2 Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_admin_approver2_remark(self):
		# To get Active id
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.travel.admin'].browse(int(active_id))
		if rec.is_extend == True or rec.is_add_advance == True or rec.is_return_trip == True:
			rec.additional_advance = 'no'
			rec.days_extension = 0
			rec.is_extend = False
			rec.travel_extend = 'no'
			rec.additional_advance_amount = 0
			rec.is_add_advance = False
			rec.return_ticket = 'no'
			rec.return_date = False
			rec.is_return_ticket = False
			rec.is_return_trip = False
			rec.app2_remarks = self.name
			rec.state = 'travelling'
			# Email - Raghu (STARTS)
			template_id = self.env.ref('hr_travel.email_template_app2_tr_reject')
			template_id.sudo().send_mail(self.id, force_send=True)
			# Email - Raghu (ENDS)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request Rejected by Approver2',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
				'hr_travel_admin_id': self.travel_id.id
			})
		elif self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				if travel_id.booking_status == 'pending':
					travel_id.write({'app2_remarks': self.name, 'state': 'cancelled'})
				elif travel_id.booking_status == 'booked':
					travel_id.write({'app2_remarks': self.name, 'state': 'travelling'})
				# Email - Raghu (STARTS)
				template_id = self.env.ref('hr_travel.email_template_app2_tr_reject')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email - Raghu (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Rejected by Approver2',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})


# Travel Admin HOD Remark

class TraveladminHODRemark(models.TransientModel):
	_name = 'travel.admin.hod.remark'
	_description = 'Travel Admin HOD Remark Wizard'

	name = fields.Text('HOD Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_admin_hod_remark(self):
		# To get Active id
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.travel.admin'].browse(int(active_id))
		if rec.is_extend == True or rec.is_add_advance == True or rec.is_return_trip == True:
			rec.additional_advance = 'no'
			rec.days_extension = 0
			rec.is_extend = False
			rec.travel_extend = 'no'
			rec.additional_advance_amount = 0
			rec.is_add_advance = False
			rec.return_ticket = 'no'
			rec.return_date = False
			rec.is_return_ticket = False
			rec.is_return_trip = False
			rec.hod_remarks = self.name
			rec.state = 'travelling'
			# Email (STARTS)
			template_id = self.env.ref('hr_travel.email_template_app2_tr_reject')
			template_id.sudo().send_mail(self.id, force_send=True)
			# Email (ENDS)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request Rejected by Approver2',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
				'hr_travel_admin_id': self.travel_id.id
			})
		elif self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				if travel_id.booking_status == 'pending':
					travel_id.write({'hod_remarks': self.name, 'state': 'cancelled'})
				elif travel_id.booking_status == 'booked':
					travel_id.write({'hod_remarks': self.name, 'state': 'travelling'})
				# travel_id.write({'hod_remarks': self.name, 'state': 'cancelled'})
				# Email (STARTS)
				template_id = self.env.ref('hr_travel.email_template_hod_tr_reject')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Rejected by HOD',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})

# Travel Admin Remark

class AdminReturnRemark(models.TransientModel):
	_name = 'travel.request.return'
	_description = 'Travel Return Wizard'

	name = fields.Text('Admin Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_return_remark(self):
		if self._context.get('is_return'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				travel_id.write({'admin_remarks': self.name, 'is_return' : True, 'state': 'submit_employee'})
				template_id = self.env.ref('hr_travel.email_template_tr_retun_employee')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Returned by Travel Admin',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.employee_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})

# Travel Admin Modify Remark

class AdminModifyRemark(models.TransientModel):
	_name = 'travel.request.modify'
	_description = 'Travel Modify Wizard'

	name = fields.Text('Admin Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_modify_remark(self):
		if self._context.get('is_modified'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				travel_id.write({'modify_remarks': self.name, 'is_modify' : True, 'is_modify_mode' : False, 'is_return' : True, 'is_return_ticket' : False, 'state': 'submit_hod'})
				template_id = self.env.ref('hr_travel.email_template_tr_mode_change')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Mode Change Request',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})

# Travel Admin Director Remarks

class AdminDirectorRemark(models.TransientModel):
	_name = 'travel.director.remarks'
	_description = 'Travel Director Reamrks'

	name = fields.Text('Director Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_director_remark(self):
		# To get Active id
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.travel.admin'].browse(int(active_id))
		if rec.is_extend == True or rec.is_add_advance == True or rec.is_return_trip == True:
			rec.additional_advance = 'no'
			rec.days_extension = 0
			rec.is_extend = False
			rec.travel_extend = 'no'
			rec.additional_advance_amount = 0
			rec.is_add_advance = False
			rec.return_ticket = 'no'
			rec.return_date = False
			rec.is_return_ticket = False
			rec.is_return_trip = False
			rec.dir_remarks = self.name
			rec.state = 'travelling'
			# Email - Raghu (STARTS)
			template_id = self.env.ref('hr_travel.email_template_director_tr_reject')
			template_id.sudo().send_mail(self.id, force_send=True)
			# Email - Raghu (ENDS)
			hr_reminder = self.env['hr.reminder'].sudo().create({
				'name': 'Travel Request Rejected By Director',
				'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
				'approver_ids': [(6, 0, self.travel_id.hr_reminder_hod_ids.ids)],
				'hr_travel_admin_id': self.travel_id.id
			})
		elif self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				if travel_id.booking_status == 'pending':
					travel_id.write({'dir_remarks': self.name, 'state': 'cancelled'})
				elif travel_id.booking_status == 'booked':
					travel_id.write({'dir_remarks': self.name, 'state': 'travelling'})
				# travel_id.write({'dir_remarks': self.name, 'state': 'cancelled'})
				# Email for TR reject- Raghu (STARTS)
				template_id = self.env.ref('hr_travel.email_template_director_tr_reject')
				template_id.sudo().send_mail(self.id, force_send=True)
				# Email for TR reject - Raghu (ENDS)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Rejected By Director',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.hr_reminder_hod_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})

# Travel Employee Cancel Remark

class EmployeeCancelRemark(models.TransientModel):
	_name = 'employee.cancel.remark'
	_description = 'Employee Cancel Remark'

	name = fields.Text('Employee Remarks')
	employee_id = fields.Many2one('hr.employee', string='Employee', related="travel_id.employee_id")
	travel_id = fields.Many2one('hr.travel.admin', 'Travel')


	@api.multi
	def action_travel_employee_remark(self):
		active_id = self.env.context.get('active_id')
		rec = self.env['hr.travel.admin'].browse(int(active_id))
		if self._context.get('is_reject'):
			for travel_id in self.env['hr.travel.admin'].browse(self._context.get('travel_id', False)):
				travel_id.write({'emp_remarks': self.name, 'is_cancel' : True, 'state': 'submit_approver1', 'cancelled' : 'Employee Cancelled'})
				template_id = self.env.ref('hr_travel.email_template_cancel_employee')
				template_id.sudo().send_mail(self.id, force_send=True)
				hr_reminder = self.env['hr.reminder'].sudo().create({
					'name': 'Travel Request Cancelled',
					'employee_id': self.employee_id.id, 'model_name': 'hr.travel.admin',
					'approver_ids': [(6, 0, self.travel_id.hr_reminder_approver1_ids.ids)],
					'hr_travel_admin_id': self.travel_id.id
				})


