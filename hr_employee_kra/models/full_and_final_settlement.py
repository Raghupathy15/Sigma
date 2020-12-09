from odoo import api, fields,models, _
from odoo.exceptions import UserError
from datetime import datetime

class FinalSettlement(models.Model):
	_name = 'final.settlement'
	_inherit = ['mail.thread']
	_description = "Final Settlement"

	employee_id = fields.Many2one('hr.employee','Employee ID',track_visibility='onchange',readonly=True)
	name = fields.Char(string="Doc No",readonly=True)
	doc_date = fields.Date('Document Date',track_visibility='onchange',readonly=True)
	designation_id = fields.Many2one('employee.designation',string="Designation",track_visibility='onchange',readonly=True)
	last_date = fields.Date('Last Date of Working',track_visibility='onchange',readonly=True)
	state = fields.Selection([('draft', 'Draft'),('approved', 'Approved')],
							 string='Status', default='draft',track_visibility='onchange',readonly=True)

	final_settlement_ids = fields.One2many('detail.payments','settlement_id',string='Final Settlement')
	
	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('final.settlement.seq')
		res = super(FinalSettlement, self).create(vals)
		return res

	@api.multi
	def action_approved(self):
		self.write({'state':'approved'})

	class DetailPayments(models.Model):
		_name = "detail.payments"

		salary_from = fields.Date('Salary From',required=True)
		salary_to = fields.Date('Salary To',required=True)
		amount = fields.Float('Amount',required=True)
		settlement_id = fields.Many2one('final.settlement',string='Final Settlement')
