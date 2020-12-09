from odoo import api, fields, models, tools, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError, UserError

class KRAProbation(models.Model):
	_inherit = "kra.probation"

	@api.multi
	def _cron_create_probation(self):
		date = datetime.date(datetime.today())
		cron_hist = self.env['cron.history']
		obj = cron_hist.create(
			{'date': date.today(), 'user_id': self.env.user.id, 'remark': 'Cron for Probation Creation'})
		create_probation = self.env['hr.employee'].sudo().search([('employment_status','=','probation')])
		var = date + relativedelta(days=15)
		for line in create_probation:
			create_probation = self.env['kra.probation'].sudo().search([('employee_id','=',line.id)])
			if not create_probation and line.probation_eval_date:
				if line.probation_eval_date <= var:
					probation = self.env['kra.probation'].create({'employee_id': line.id,})
					template_id = self.env.ref('cron_probation.email_template_probation_creation')
					template_id.send_mail(probation.id, force_send=True)
			elif not create_probation and line.probation_eval_date1:
				if line.probation_eval_date1 <= var:
					probation = self.env['kra.probation'].create({'employee_id': line.id,})
					template_id = self.env.ref('cron_probation.email_template_probation_creation')
					template_id.send_mail(probation.id, force_send=True)
		return True

class UserBlockedKRA(models.Model):
	_inherit = "hr.kra"

	@api.model
	def _cron_block_user(self):
		exist_emp = []
		date = datetime.date(datetime.today())
		var = date + relativedelta(days=-7)
		for vals in self.env['hr.employee'].search([('employment_status', '=', 'probation')]):
			exist_emp.append(vals)
			if vals.joining_date < var and vals.kra_count == 0:
				for app1 in vals.lone_manager_id:
					if app1.is_blocked == False:
						app1.user_id.is_blocked = True
						template_id = self.env.ref('cron_probation.email_template_kra_creation')                
						template_id.send_mail(vals.id, force_send=True)
				return True

class KRAQuarterly(models.Model):
	_inherit = "kra.quarterly"

	@api.model
	def _cron_creation_quarterly(self):
		date = datetime.date(datetime.today())
		var = date + relativedelta(months= -3)
		var_1 = date + relativedelta(months= -13)
		var_2 = date + relativedelta(months= -14)
		var_3 = date + relativedelta(months= -15)
		month_1 = var_1.strftime('%b')
		month_2 = var_2.strftime('%b')
		month_3 = var_3.strftime('%b')
		create_form = self.env['hr.employee'].search([('active', '=', True)])
		for line in create_form:
			if line.joining_date:
				join = line.joining_date.strftime('%b')
				if line.joining_date < var:
					if month_1 != join and month_2 != join and month_3 != join:
						kra = self.env['hr.kra'].search([('employee_id', '=', line.id),('state', '=', 'done')],order="id desc", limit=1)
						no_create = date + relativedelta(months= -3)
						quart = self.env['kra.quarterly'].search([('employee_id', '=', line.id),('date', '>', no_create)])
						if not quart:
							quarterly = self.env['kra.quarterly'].create({
								'employee_id': line.id,
								'kra_id': kra.id,
								'employee_ids': line.id,
								})
							# Reminder Notification
							hr_reminder = line.env['hr.reminder'].sudo().create({
								'name': 'Quaterly review is created for you',
								'employee_id': line.id, 'model_name': 'kra.quarterly',
								'approver_ids': [(6, 0, quarterly.employee_ids.ids)],
								'kra_quarterly_appraisal_id': quarterly.id
							})
							# print ('QQQQQQQQQQQQ', quarterly)
							kra = self.env['hr.kra'].search([('employee_id', '=', line.id),('state', '=', 'done')],order="id desc", limit=1)
							kra_line = kra.mapped('kra_line_ids')
							for vals in kra_line:
								quart_line = self.env['quarterly.review'].create({
									'kra': vals.name,
									'details_kra': vals.details,
									'timeline_id': vals.timeline_id.id,
									'weightage': vals.target,
									'review_id': quarterly.id,
									})
							# template_id = self.env.ref('cron_probation.email_template_quarterly_creation')
							# template_id.write({'email_to' : line.work_email})
							# template_id.send_mail(quarterly.id, force_send=True)
		return True

	@api.model
	def _cron_quarterly_block_employee(self):
		exist_emp = []
		date = datetime.date(datetime.today())
		print (date)
		var = date + relativedelta(days=-7)
		for vals in self.env['hr.employee'].search([('active', '=', True)]):
			exist_emp.append(vals)
			for line in vals.quarterly_ids:
				if line.seq_date:
					print ('SSSSSSSSSSSS', vals)
				if vals.joining_date < var and vals.kra_count == 0:
					for app1 in vals.lone_manager_id:
						if app1.is_blocked == False:
							app1.user_id.is_blocked = True
							template_id = self.env.ref('cron_probation.email_template_kra_creation')
							template_id.send_mail(vals.id, force_send=True)
					return True
					
class KRAAnnual(models.Model):
	_inherit = "kra.appraisal"

	@api.model
	def _cron_create_annual(self):
		date = datetime.date(datetime.today())
		var_1 = date + relativedelta(months= -13)
		var_2 = date + relativedelta(months= -14)
		var_3 = date + relativedelta(months= -15)
		month_1 = var_1.strftime('%b')
		month_2 = var_2.strftime('%b')
		month_3 = var_3.strftime('%b')
		create_form = self.env['hr.employee'].search([('active', '=', True)])
		for line in create_form:
			if line.joining_date:
				join = line.joining_date.strftime('%b')
				if month_1 == join or month_2 == join or month_3 == join and line.joining_date < var_1:
					no_create = date + relativedelta(months= -3)
					ann = self.env['kra.appraisal'].search([('employee_id', '=', line.id)])
					if not ann:
						annual = self.env['kra.appraisal'].create({
							'employee_id': line.id,
							'employee_ids': line.id,
							})
						# Reminder Notification
						hr_reminder = line.env['hr.reminder'].sudo().create({
							'name': 'Annual assessment is created for you',
							'employee_id': line.id, 'model_name': 'kra.appraisal',
							'approver_ids': [(6, 0, annual.employee_ids.ids)],
							'kra_annual_appraisal_id': annual.id
						})
						kra = self.env['hr.kra'].search([('employee_id', '=', line.id),('state', '=', 'done')],order="id desc", limit=1)
						kra_line = kra.mapped('kra_line_ids')
						for vals in kra_line:
							annual_line = self.env['annual.appraisal'].create({
								'kra': vals.name,
								'details_kra': vals.details,
								'timeline_id': vals.timeline_id.id,
								'weightage': vals.target,
								'appraisal_id': annual.id,
								})
							line.write({'appraisal_date': date.today()})
							template_id = self.env.ref('cron_probation.email_template_annual_creation')
							template_id.write({'email_to' : line.work_email})
							template_id.send_mail(annual.id, force_send=True)
		return True
