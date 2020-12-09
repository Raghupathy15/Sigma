from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class ScheduleActivities(models.Model):
	_name = "schedule.activities"

	sch_id = fields.Many2one('crm.lead',string='Unblocked')
	name = fields.Char('Description',readonly=False)
	activity_type_id = fields.Many2one('mail.activity.type', 'Activity')
	date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today)
	summary = fields.Char('Summary')
	user_id = fields.Many2one('res.users', 'Assigned to', default=lambda self: self.env.user,index=True, required=True)

class LeadCRM(models.Model):
	_inherit = "crm.lead"
	_description = "Lead/Opportunity"

	seq_no = fields.Char("Seq") 
	po_num = fields.Char("PO No") 
	po_date = fields.Date("PO Date")
	po_rec_date = fields.Date("PO Recieved Date")
	usd_order_value = fields.Float("USD Order Value")
	inr_order_value = fields.Float("INR Order Value")
	supply_order_value = fields.Float("Supply Order Value")
	service_order_value = fields.Float("Service Order Value")
	product_description = fields.Char("Product Description")
	supply_order = fields.Boolean("Supply Order")
	service_order = fields.Boolean("Service Order")
	payment_terms = fields.Char("Payment Terms")
	delivery_time = fields.Char("Delivery Time")
	additional_requirement = fields.Boolean("Additional")
	so_no_in_sap = fields.Char("SO No in SAP")
	severity = fields.Selection([('hot', 'Hot'),('warm', 'Warm'),('cold', 'Cold')], "Severity")

	acti_ids = fields.One2many('schedule.activities','sch_id',string='Scheduled Activities')

	#added
	@api.model
	def create(self,vals):
		vals['seq_no'] = self.env['ir.sequence'].next_by_code('crm.lead')
		rec = super(LeadCRM,self).create(vals)
		return rec

	@api.multi
	@api.constrains('po_date')
	def _check_po_date(self):
		for vals in self:
		# if vals.employee_rating > vals.max_rating or vals.l1 > vals.max_rating or vals.l2 > vals.max_rating:
			if vals.po_rec_date < vals.po_date:
				raise ValidationError(_("Recieved Date should be greater than PO Date..."))
		return True

	@api.multi
	def button_create(self):
		for crm_id in self.env['crm.lead'].search([('active','=',True)]):
			act = self.env['mail.activity'].search([('res_name','=',crm_id.name)])
			if act:
				for activity in act:
					crm_1 = self.env['schedule.activities'].search([('sch_id', '=', crm_id.id),('name', '=',activity.note[3:-4])])
					if not crm_1:
						create = crm_id.acti_ids.create({'sch_id': crm_id.id,'name': activity.note[3:-4],
													'activity_type_id': activity.activity_type_id.id,
													'date_deadline': activity.date_deadline,
													'summary': activity.summary,
													'user_id': activity.user_id.id})					

class PartnerRES(models.Model):

	_inherit = 'res.partner'

	customer_location = fields.Char("Customer Location")
	city_id = fields.Many2one('city.master',string="City")

	@api.multi
	def name_get(self):
		result = []
		for line in self:
			name = str(line.seq_no) + ' - ' + line.name
			result.append((line.id, name))
		return result

	@api.model
	def create(self,vals):
		vals['seq_no'] = self.env['ir.sequence'].next_by_code('res.partner')
		rec = super(PartnerRES,self).create(vals)
		return rec

	@api.onchange('city_id')
	def onchange_city(self):
		if self.city_id:
			self.city = self.city_id.name
			self.state_id = self.city_id.state_id.id

	@api.depends('name')
	def compute_employee_id(self):
		for rec in self:
			employee_rec = self.env['res.users'].sudo().search([('partner_id', '=', rec.id)], limit=1)
			rec.employee_id = employee_rec.employee_id.id
			rec.seq_no = employee_rec.employee_id.employee_id

	employee_id = fields.Many2one("hr.employee", string="Employee", compute="compute_employee_id")
	seq_no = fields.Char("Seq", compute="compute_employee_id")

	# Auto create seq no for imported data
	# @api.multi
	# def action_create_seq(self):
	# 	sequence = 0
	# 	seq = 0
	# 	if self.name:
	# 		res = self.env['res.partner'].search([('customer','=',False)])
	# 		for data in res:
	# 			seq += sequence + 1
	# 			print ('==================',data)
	# 			data.seq_no = 'EMP'+ str(seq)
	# 			print ('==================',seq)