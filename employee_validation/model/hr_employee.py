from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, _
import re


class HrEmployee(models.Model):
	_inherit = 'hr.employee'	

	@api.multi
	@api.constrains('contact_no')
	def _check_phone_number(self):
		for rec in self:
			if rec.contact_no and len(rec.contact_no) != 10:
				raise ValidationError(_("Please Enter 10 digit Contact Numbers..."))
		return True

	@api.onchange('employee_email','work_email','name')
	def validate_mail(self):
		if self.employee_email or self.work_email:
			match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.employee_email or self.work_email)
			#match = re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", self.employee_email)
			if match == None:
				raise ValidationError('Not a valid E-mail ID')
		if self.name:
			match1 = re.match('^[_a-zA-Z][_a-zA-Z]*', self.name)
			#match = re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", self.employee_email)
			if match1 == None:
				raise ValidationError('Enter only Aplhabets')

class HrApplicant(models.Model):
	_inherit = 'hr.applicant'

	@api.onchange('email_from','name')
	def validate_mail(self):
		if self.email_from:
			match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email_from)
			#match = re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", self.employee_email)
			if match == None:
				raise ValidationError('Not a valid E-mail ID')
		if self.name:
			match = re.match('^[_a-zA-Z][_a-zA-Z]*', self.name)
			#match = re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", self.employee_email)
			if match == None:
				raise ValidationError('Enter only Aplhabets')

	@api.multi
	@api.constrains('partner_mobile')
	def _check_phone_number(self):
		for rec in self:
			if rec.partner_mobile and len(rec.partner_mobile) != 10:
				raise ValidationError(_("Please Enter 10 digit Contact Number..."))
		return True

# class HrMrf(models.Model):
# 	_inherit = 'hr.mrf'

	
# 	@api.constrains('request_date','closure_date')
# 	def _check_date_validation(self):
# 		for rec in self:
# 			if rec.request_date and rec.closure_date:
# 				if rec.request_date > rec.closure_date:
# 					raise ValidationError(_("Date of Request Should not be Greter then Closure Timeline..."))
# 		return True

# class QuarterlyReview(models.Model):
# 	_inherit = 'quarterly.review'

	
# 	@api.constrains('employee_rating','max_rating')
# 	def _check_rating(self):
# 		# print('ddd')
# 		for rec in self:
# 			if rec.employee_rating > rec.max_rating:
# 				raise ValidationError(_("Rating Should not be Greater than 10..."))
# 		return True



