# -*- coding: utf-8 -*-
from odoo import fields, models, api
import calendar
from datetime import datetime
from odoo.exceptions import Warning

MONTHS = [('01', 'January'),
		  ('02', 'February'),
		  ('03', 'March'),
		  ('04', 'April'),
		  ('05', 'May'),
		  ('06', 'June'),
		  ('07', 'July'),
		  ('08', 'August'),
		  ('09', 'September'),
		  ('10', 'October'),
		  ('11', 'November'),
		  ('12', 'December')]

class MultiPayslip(models.TransientModel):
	_name = 'multi.payslip'
	_description = 'Multi Payslip'

	payslip_date = fields.Selection(MONTHS, 'Month From', required=True)

	@api.multi
	def action_generate_payslip(self):
		now = datetime.now()
		mon_from = int(self.payslip_date)
		last_day_of_month = calendar.monthrange(
			now.year, mon_from)[1]
		date_str = str(now.year) + '-' + \
			str(mon_from) + '-' + str(last_day_of_month)
		first_date = datetime.strptime(
			str(now.year) + '-' + str(mon_from) + '-' + '01',
			'%Y-%m-%d')
		last_date = datetime.strptime(date_str, '%Y-%m-%d')
		if mon_from >= now.month:
			raise Warning(
				('Please select correct month less then '
					'current month.'))
		for emp_id in self.env['hr.employee'].search([('active', '=', True),('payroll', '=', 'yes')]):
			contract_id_obj = self.env['hr.contract'].search(
			[('employee_id', '=', emp_id.id),
			 ('state', 'in', ['open'])], order="date_start desc", limit=1)
			if not emp_id.contract_id:
				raise Warning(
					('Please Create Contract for employee = %s.') %
					emp_id.name)
			val = {'employee_id': emp_id.id,
				   'name': emp_id.name + ' \'s Payslip',
				   'contract_id': emp_id.contract_id.id,
				   'struct_id': emp_id.struct_id.id,
				   'date_from': first_date,
				   'date_to': last_date,
				   }
			vals = self.env['hr.payslip'].search([('date_from', '=', first_date),('date_to', '=', last_date),('employee_id', '=', emp_id.id)])
			if not vals:
				self.env['hr.payslip'].create(val)

	@api.multi
	def compute_sheet_payslip(self):
		now = datetime.now()
		mon_from = int(self.payslip_date)
		last_day_of_month = calendar.monthrange(
			now.year, mon_from)[1]
		date_str = str(now.year) + '-' + \
			str(mon_from) + '-' + str(last_day_of_month)
		first_date = datetime.strptime(
			str(now.year) + '-' + str(mon_from) + '-' + '01',
			'%Y-%m-%d')
		last_date = datetime.strptime(date_str, '%Y-%m-%d')
		pay = self.env['hr.payslip'].search([('date_from', '=', first_date),('date_to', '=', last_date)])
		if pay:
			for payslip in pay:
				number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
				# delete old payslip lines
				payslip.line_ids.unlink()
				# set the list of contract for which the rules have to be applied
				# if we don't give the contract, then the rules to apply should be for all current contracts of the employee
				contract_ids = payslip.contract_id.ids or \
					payslip.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
				lines = [(0, 0, line) for line in payslip._get_payslip_lines(contract_ids, payslip.id)]
				payslip.write({'line_ids': lines, 'number': number})
		else:
			raise Warning(
				('Please Generate Payslip for that month.'))
		return True

	@api.multi
	def action_confirm_payslip(self):
		now = datetime.now()
		mon_from = int(self.payslip_date)
		last_day_of_month = calendar.monthrange(
			now.year, mon_from)[1]
		date_str = str(now.year) + '-' + \
			str(mon_from) + '-' + str(last_day_of_month)
		first_date = datetime.strptime(
			str(now.year) + '-' + str(mon_from) + '-' + '01',
			'%Y-%m-%d')
		last_date = datetime.strptime(date_str, '%Y-%m-%d')
		self.compute_sheet_payslip()
		for payslip in self.env['hr.payslip'].search([('date_from', '=', first_date),('date_to', '=', last_date)]):
			if payslip.loan > 0:
				for loan in self.env['loan.deduction'].search([('employee_id', '=', payslip.employee_id.id),('state', '=', 'submitted')]):
					for vals in loan.installment_ids:
						if payslip.date_from <= vals.payment_date and payslip.date_to >= vals.payment_date:
							vals.payment_status = 'paid'
					if payslip.date_from >= loan.date_to and payslip.date_from <= loan.date_to:
						loan.state = 'done'
			payslip.write({'state': 'done'})
		return True
