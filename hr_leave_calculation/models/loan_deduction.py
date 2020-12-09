# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

class LoanDeduction(models.Model):
	_name = 'loan.deduction'

	name = fields.Char(default='New', copy=False, readonly=True, string="Name")
	state = fields.Selection([('draft', 'Draft'),('submitted', 'Submitted'),('done', 'Done')],
		string='Status', default='draft',track_visibility='onchange')
	employee_id = fields.Many2one('hr.employee', string="Employee Name", required=True)
	user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
	advance_amount = fields.Float(string="Advance Amount")
	payable_amount = fields.Float(string="Payable Amount", readonly=True)
	no_of_installment = fields.Integer(string="No of Installment", required=True)
	creation_date = fields.Date(string="Creation Date", default=fields.Date.context_today, readonly=True)
	date_from = fields.Date(string="From Date", required=True)
	date_to = fields.Date(string="End Date", required=True)
	nature_from = fields.Char(string="Nature of Advance", required=True)
	installment_ids = fields.One2many('loan.installment', 'loan_id', string="Installment")

	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('loan.deduction')
		rec = super(LoanDeduction,self).create(vals)
		return rec

	@api.multi
	@api.onchange('advance_amount', 'no_of_installment')
	def onchange_payable_amount(self):
		if self.advance_amount and self.no_of_installment:
			self.payable_amount = self.advance_amount/self.no_of_installment
			self.date_to = self.date_from + relativedelta(months=(self.no_of_installment)-1)

	@api.multi
	def action_submit(self):
		var = self.date_from
		for line in range(0, self.no_of_installment):
			install = self.env['loan.installment'].create({
				'payment_date': var,
				'amount': self.payable_amount,
				'payment_status': 'pending',
				'loan_id': self.id,
				})
			var = var + relativedelta(months=1)
		self.state = 'submitted'
	
class LoanEmiCalc(models.Model):
	_name = 'loan.installment'

	loan_id = fields.Many2one('loan.deduction', string="Name")
	date = fields.Date(string="Date")
	payment_status = fields.Selection([('pending', 'Pending'),('paid', 'Paid')],
							 string='Payment Status', default='pending')
	payment_date = fields.Date(string="Payment Date")
	amount = fields.Float(string="Amount")

