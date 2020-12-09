from odoo import api, fields, models


class TdsGroup(models.Model):
	_name = 'tds.group'
	_description = 'TDS Group'
	name = fields.Char(string="Section")
	amount = fields.Float(string="Amount")
	group_ids = fields.One2many('tds.group.line','group_id')
	

class TdsGroupLine(models.Model):
	_name = 'tds.group.line'
	_description = 'TDS Group Line'

	group_id = fields.Many2one('tds.group')

	section_id = fields.Many2one('tds.section',string="Section")
	description = fields.Char(string="Description",related="section_id.description",readonly=True)


class TdsSection(models.Model):
	_name = 'tds.section'
	_description = 'TDS Section'
	name = fields.Char(string="Section")
	description = fields.Char(string="Description")
	tds_group_id = fields.Many2one('tds.group',string="Group")

class TdsMaster(models.Model):
	_name = 'tds.master'
	_description = 'TDS Master'

	name = fields.Char(string="Code")
	description = fields.Char(string="Description")
	section = fields.Char(string="Section")
	potential = fields.Float(string="Potential")
	financial_year_from = fields.Date(string="Financial Year")
	financial_year_to = fields.Char(string="Financial Year To",compute="fetch_next_year")

	@api.multi
	@api.depends('financial_year_from')
	def fetch_next_year(self):
		date = month = year = to_year = day = converted_date = 0
		for line in self:
			if line.financial_year_from:
				date = str(line.financial_year_from)
				year = date[:4]
				to_year = int(year)+1
				month = date[5:7]
				day = date[8:10]
				converted_date = month +'/'+ day +'/'+ str(to_year)
				line.financial_year_to = converted_date



class TdsCalculation(models.Model):
	_name = 'tds.calculation'
	_description = 'TDS Calculation'

	name = fields.Many2one('tds.master',string="Code")
	description = fields.Char(string="Description",related="name.description")
	financial_year_from = fields.Date(string="Financial Year",related="name.financial_year_from")
	financial_year_to = fields.Char(string="Financial Year To",related="name.financial_year_to")
	section = fields.Char(string="Section",related="name.section")
	potential = fields.Float(string="Potential",related="name.potential")
	actual = fields.Float(string="Actual")
	gap = fields.Float(string="GAP",compute="calculate_gap")
	employee_id = fields.Many2one('hr.employee',string="Employee")


	@api.multi
	@api.depends('potential','actual')
	def calculate_gap(self):
		for line in self:
			if line.potential and line.actual:
				line.gap = line.potential - line.actual

