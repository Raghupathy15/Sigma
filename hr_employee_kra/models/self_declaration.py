# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

YEARS = []
for year in range(int(date.today().strftime('%Y')) - 4 , int(date.today().strftime('%Y')) + 1):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
		  ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
		  ('11', 'November'), ('12', 'December')]

class SelfDeclarationMaster(models.Model):
	_name = 'self.declaration.master'

	name = fields.Char(string="Name")
	proof_required = fields.Char(string="Proof required")
	tds_group_id = fields.Many2one('tds.group',string="Section")
	section_id = fields.Many2one('tds.section',string="Section")
	limit = fields.Float(string="Allowed Limit")
	active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the Self Declaration master without removing it.")


class SelfDeclaration(models.Model):
	_name = 'self.declaration'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_order = 'id desc'

	@api.model
	def _default_clearance_line(self):
		master = self.env['self.declaration.master']
		vals = []
		master_ids = master.search([])

		for line in master_ids:
			data={}
			data['name'] = line.name
			data['section_id'] = line.section_id.id
			data['section_amount'] = line.section_id.tds_group_id.amount
			data['limit'] = line.limit
			data['tds_group_id'] = line.section_id.tds_group_id.id
			data['tds_group_amount'] = line.section_id.tds_group_id.amount
			data['proof_required'] = line.proof_required
			vals.append((0,0,data))
		return vals

	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)


	name = fields.Char(string="Doc No.")
	seq_date = fields.Datetime(string="Seq Date",default=lambda self: fields.datetime.now())
	employee_id = fields.Many2one('hr.employee', string="Employee Name", default=_default_employee)
	employee_code = fields.Char(string="Employee Id",related="employee_id.employee_id",store=True)
	pan = fields.Char(string="PAN",related="employee_id.pan")
	account_no = fields.Char(string="Bank Acc No.",related="employee_id.account_no")
	birthday = fields.Date(string="Date of Birth",related="employee_id.birthday")
	job_id = fields.Many2one('employee.designation',string="Designation",related="employee_id.designation_id")
	department_id = fields.Many2one('hr.department',string="Department",related="employee_id.department_id")
	
	declaration_line_ids = fields.One2many('self.declaration.line','declaration_id',default = _default_clearance_line)
	sum_amount = fields.Float(string="Total Amount",compute="fetch_sum_total")
	from_year = fields.Selection(YEARS, string="Year of Request", default=date.today().strftime('%Y'))
	processing_month = fields.Selection(PERIOD, string="Required Month", default=date.today().strftime('%m'))
	doc_date = fields.Date(string='Doc Date',default=datetime.today().strftime('%Y-%m-%d'))
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	self_declare_edit = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
										 string="Allowance to Edit Self Declaration",
										 related='employee_id.self_declare_edit')
	self_declare_document = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
											 string="Allowance to Upload Document in Self Declaration",
											 related='employee_id.self_declare_document')

	@api.depends('employee_id')
	def compute_self_dec(self):
		for vals in self:
			if vals.self_declare_edit == 'no' and vals.self_declare_document == 'no':
				vals.delcalration_acces_no = True

	delcalration_acces_no = fields.Boolean(string="Both Declaration Access NO", compute="compute_self_dec",default=False)

	@api.multi
	@api.depends('declaration_line_ids.amount','declaration_line_ids.tds_group_id')
	def fetch_sum_total(self):
		for line in self:
			total = 0.0
			for lines in line.declaration_line_ids:
				section_id = self.env['tds.section'].search([('id','=',lines.section_id.id)])
				if section_id:
					max_amount = total_sec_amount = 0
					for sec in section_id:
						max_amount = sec.tds_group_id.amount
						# raise UserError(_('Max Amount is . %s')%(max_amount))
						for line_sec in line.declaration_line_ids:
							if sec.id == line_sec.section_id.id:
								total_sec_amount += line_sec.amount
						if max_amount < total_sec_amount:
							raise UserError(_('Maximum Limit of amount for the Section %s is %s. Sum amount exceeds the limit')%(sec.name,max_amount))
				total += lines.amount
			line.update({
					'sum_amount': total,
				})

	
	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('self.declaration')
		rec = super(SelfDeclaration,self).create(vals)
		return rec

class SelfDeclarationLine(models.Model):
	_name = 'self.declaration.line'
	# _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	declaration_id = fields.Many2one('self.declaration')

	sl_no = fields.Integer(string="Sl. No.",compute="fetch_sl_no")
	name = fields.Char(string="Description")
	proof_required = fields.Char(string="Proof required")
	tds_group_id = fields.Many2one('tds.group',string="Group")
	tds_group_amount = fields.Float(string="Potential",readonly=False)
	limit = fields.Float(string="Allowed Limit")
	section_id = fields.Many2one('tds.section',string="Section")
	section_amount = fields.Float(string="Section Amount",readonly=False)
	sub_amount = fields.Float(string="Amount")
	amount = fields.Float(string="Taxable Amount",store=True,compute="fetch_final_amount")
	upload_file = fields.Binary(string="Attachment (Max~3MB)")
	file_name = fields.Char(string="Attachment File Name")
	self_declare_edit = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
										 string="Allowance to Edit Self Declaration",
										 related='declaration_id.self_declare_edit')
	self_declare_document = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
											 string="Allowance to Upload Document in Self Declaration",
											 related='declaration_id.self_declare_document')
	delcalration_acces_no = fields.Boolean(string="Both Declaration Access NO", related='declaration_id.delcalration_acces_no')

	@api.multi
	@api.depends('sub_amount','limit')
	def fetch_final_amount(self):
		for line in self:
			if line.limit > 0:
				if line.sub_amount > line.limit:
					line.amount = line.limit
				else:
					line.amount = line.sub_amount
			else:
				line.amount = line.sub_amount


	def fetch_sl_no(self):
		sl = 0
		if self.ids:
			line_id = self.browse(self.ids[0])
			for line in line_id.declaration_id.declaration_line_ids:
				sl = sl + 1
				line.sl_no = sl

