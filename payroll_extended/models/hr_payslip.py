# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import datetime
import dateutil.parser
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import calendar
from calendar import monthrange

class CustomHrPayslip(models.Model):
	_inherit = 'hr.payslip'
	
	leave_id = fields.One2many('hr.payslip.leave','leave_payslip_ids')
	leave_update_bool = fields.Boolean(string="Update Leave",default=False)
	leave_update_salary_bool = fields.Boolean(string="Update Salary",default=False)
	num_of_days_worked = fields.Float(string="Number of days Worked in a Month", compute="compute_holidays", store=True)
	days_in_current_month = fields.Float(string="Number of Days in a Month", compute="compute_days_in_month", store=True)
	num_of_global_leaves = fields.Float(string="Number of Global Holidays in a Month", compute="compute_holidays")
	num_of_weekoffs = fields.Float(string="Weekoffs", compute="compute_holidays", store=True)
	num_of_leaves = fields.Float(string="Number of Leaves Taken", compute="compute_holidays", store=True)
	num_of_lop = fields.Float(string="Total Days of LOP", compute="compute_holidays", store=True)
	vpf = fields.Float(string="VPF")
	tds = fields.Float(string="TDS")
	# ctc = fields.Float(string="CTC")
	loan = fields.Float(string="Salary Advance", compute="compute_loan_amount", store=True)
	other_earnings = fields.Float(string="Other Earnings")
	other_deduction = fields.Float(string="Other Deduction")
	struct_id = fields.Many2one('hr.payroll.structure', string='Grade',
		 states={'draft': [('readonly', False)]},
		help='Defines the rules that have to be applied to this payslip, accordingly '
			 'to the contract chosen. If you let empty the field contract, this field isn\'t '
			 'mandatory anymore and thus the rules applied will be all the rules set on the '
			 'structure of all contracts of the employee valid for the chosen period',related="contract_id.struct_id")
	check_bool = fields.Boolean(string='Check',readonly=True)
	#days_list = fields.Char(string="Days List",compute="fetch_days_in_month")
	_ctc = fields.Float(string='CTC', compute="_compute_line_vals")
	_gross = fields.Float(string='Gross', compute="_compute_line_vals")
	_basic = fields.Float(string='Basic', compute="_compute_line_vals")
	_lop = fields.Float(string='LOP', compute="_compute_line_vals")
	_total_deduction = fields.Float(string='Total Deduction', compute="_compute_line_vals")
	_amt_payable = fields.Float(string='Amount Payable', compute="_compute_line_vals")
	designation_id = fields.Many2one('employee.designation', string='Designation', related="employee_id.designation_id")
	location_work_id = fields.Many2one('work.location', string="Work Location",related="employee_id.location_work_id")
	joining_date = fields.Date(string='DOJ', related='employee_id.joining_date')

	@api.multi
	@api.depends('line_ids')
	def _compute_line_vals(self):
		for order in self:
			order._ctc = order.line_ids.filtered(lambda l: l.code == 'CTC').amount
			order._gross = order.line_ids.filtered(lambda l: l.code == 'GPM').amount
			order._basic = order.line_ids.filtered(lambda l: l.code == 'BASIC').amount
			order._lop = order.line_ids.filtered(lambda l: l.code == 'LOP').amount
			order._total_deduction = order.line_ids.filtered(lambda l: l.code == 'TDE').amount
			order._amt_payable = order.line_ids.filtered(lambda l: l.code == 'AMT').amount

	@api.multi
	@api.depends('employee_id','date_from','date_to')
	def compute_loan_amount(self):
		for amount in self:
			for loan in self.env['loan.deduction'].search([('employee_id', '=', amount.employee_id.id),('state', '=', 'submitted')]):
				for vals in loan.installment_ids:
					if amount.date_from <= vals.payment_date and amount.date_to >= vals.payment_date:
						amount.loan = vals.amount

	@api.multi
	@api.depends('date_from','date_to', 'employee_id')
	def compute_days_in_month(self):
		total_sum = 0
		lists =[]
		for line in self:
			start_dt = fields.Datetime.from_string(line.date_from)
			line.days_in_current_month = monthrange(start_dt.year,start_dt.month)[1]

	#added
	@api.multi
	def action_payslip_done(self):
		res = super(CustomHrPayslip, self).action_payslip_done()
		for payslip in self:
			if payslip.loan > 0:
				for loan in self.env['loan.deduction'].search([('employee_id', '=', payslip.employee_id.id),('state', '=', 'submitted')]):
					for vals in loan.installment_ids:
						if payslip.date_from <= vals.payment_date and payslip.date_to >= vals.payment_date:
							vals.payment_status = 'paid'
					if payslip.date_from >= loan.date_to and payslip.date_from <= loan.date_to:
						loan.state = 'done'
		return True

	@api.model
	@api.depends('employee_id')
	def compute_holidays(self):
		import datetime
		for line in self:
			present_days = leave_count = total_count = deduct_count = 0.0
			approved_leave_count = weekoff_count = global_count = 0.0
			if line.employee_id:
				start_dt = line.date_from
				day = datetime.date(start_dt.year, start_dt.month, 1)
				single_day = datetime.timedelta(days=1)
				sundays = 0
				while day.month == start_dt.month:
				   if day.weekday() == 6:
					   sundays += 1
				   day += single_day
				print ('Sundays:', sundays)
				weekoff_count = sundays
				line.num_of_weekoffs = weekoff_count
				#fetch number of entries in a date range
				for attendance in self.env['hr.attendance'].search([('employee_id','=',line.employee_id.id)]):
					if attendance:
						for attr in attendance:
							#check for an attendance exists in between the month selected in payslip
							if attr.check_in:
								check_in = attr.check_in.date()
								if check_in >= line.date_from and check_in <= line.date_to:
									present_days = present_days + float(attr.present_day_status)
								line.num_of_days_worked = present_days

				#fetch number of leaves in a date range
				# hr_leave = self.env['hr.leave'].sudo().search([('company_id','=',line.company_id.id),('employee_id','=',line.employee_id.id)])
				for hr_leave in self.env['hr.leave'].sudo().search([('employee_id','=',line.employee_id.id),('state','=','validate')]):
					if hr_leave:
						for leaves in hr_leave:
							if leaves.request_date_from >= line.date_from and leaves.request_date_to <= line.date_to:
								for attr in attendance:
									check_in = attr.check_in.date()
									if check_in == leaves.request_date_from:
										approved_leave_count = approved_leave_count + leaves.number_of_days_display
								leave_count = leave_count + leaves.number_of_days_display
						line.num_of_leaves = leave_count
					
				#fetch global leaves count
				for resource_calendar_leaves in self.env['resource.calendar.leaves'].sudo().search([('company_id','=',line.company_id.id),('work_location_id','=',line.employee_id.location_work_id.id)]):
					if resource_calendar_leaves:
						for leaves in resource_calendar_leaves:
							if leaves.from_date >= line.date_from and leaves.to_date <= line.date_to:
								global_count = global_count + leaves.days_count
						line.num_of_global_leaves = global_count

				total_count = line.num_of_days_worked + line.num_of_leaves + line.num_of_weekoffs + line.num_of_global_leaves
				if total_count < float(line.days_in_current_month):
					deduct_count = float(line.days_in_current_month) - total_count
					line.num_of_lop = float(deduct_count)



	@api.multi
	def leaves_update_button(self):
		for line in self:
			line.leave_id.unlink()
			#add total entries
			total_count = line.num_of_days_worked + line.num_of_leaves + line.num_of_weekoffs + line.num_of_global_leaves
			if total_count < float(line.days_in_current_month):
				deduct_count = float(line.days_in_current_month) - total_count
				# line.num_of_lop = float(deduct_count)
				leave_line = self.env['hr.payslip.leave']
				vals ={}
				vals = {
				'leaves_taken':line.num_of_lop,
				'leave_payslip_ids':line.id,
				}
				leave_line.create(vals)
				line.leave_update_bool = True
				# line.compute_sheets()	

	@api.multi
	def compute_sheet_payslip(self):
		for payslip in self.env['hr.payslip'].search([]):
			number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
			# delete old payslip lines
			payslip.line_ids.unlink()
			# set the list of contract for which the rules have to be applied
			# if we don't give the contract, then the rules to apply should be for all current contracts of the employee
			contract_ids = payslip.contract_id.ids or \
				self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
			lines = [(0, 0, line) for line in payslip._get_payslip_lines(contract_ids, payslip.id)]
			payslip.write({'line_ids': lines, 'number': number})
		return True
		# 	payslip.compute_sheet()
		# 	# res = super(CustomHrPayslip, self).compute_sheet()
		
		# return True


