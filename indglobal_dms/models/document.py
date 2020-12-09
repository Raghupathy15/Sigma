# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import date,datetime
from odoo.exceptions import UserError

class Document(models.Model):
	_name = "indglobal.document"
	_description = 'Document'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	active = fields.Boolean(default=True)
	sequence = fields.Char('Document No')
	name = fields.Char('Name', required=True)
	content = fields.Html('Content')
	attach = fields.Binary('Attachment (Max~3MB)')
	attachment = fields.Char('Document No')
	created_date = fields.Date('Created Date',readonly=True,default=fields.Date.today())
	created_user_id = fields.Many2one('res.users',readonly=True,string='Created By',default=lambda self: self.env.uid)
	doc_mode = fields.Selection([('hr', 'HR'),('emp', 'Employee')], string='Document Mode')

	_sql_constraints = [
		('name', 'unique(name)', 'Name already exists!'),
	]

	# Sequence Generation		
	@api.model
	def create(self, vals):
		vals['sequence'] = self.env['ir.sequence'].next_by_code('doc.seq') or '/'
		return super(Document, self).create(vals)