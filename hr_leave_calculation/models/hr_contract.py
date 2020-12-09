# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, fields, models, _


class HrContract(models.Model):
	_inherit = 'hr.contract'

	mobile_conveyance = fields.Monetary('Mobile/Conveyance/Internet', digits=(16, 2), track_visibility="onchange")
	city_allowance = fields.Monetary('City Compensatory ALLOWANCE', digits=(16, 2), required=True, track_visibility="onchange")
	esi_calc = fields.Boolean('ESI Calculation', track_visibility="onchange")
	proposed_ctc = fields.Float(string="Offered CTC" ,digits=(16, 0),track_visibility="onchange", compute="compute_salary")

	@api.depends('struct_id','wage')
	def compute_salary(self):
		for line in self:
			basic_amount = insurance_amount = hra_amount = pf_amount = pf_amount_emp = esic_amount= esi_amount= 0
			mobile_conveyance = city_allowance = special_amount = gratuity_amount = bonus_amount =0
			gross_amount = pt_amount= 0
			#Basic salary calculation
			if line.struct_id.name:
				basic_amount = round(line.struct_id.basic_amount)
				insurance_amount = round(line.struct_id.insurance_amount)
				hra_amount = round(basic_amount*40/100)
			#Special Allowance Calculation
			special_amount = line.wage- (basic_amount+hra_amount+line.mobile_conveyance+line.city_allowance)
			#Mobile allowance
			if line.mobile_conveyance:
				mobile_conveyance = line.mobile_conveyance
			#City Allowance
			if line.city_allowance:
				city_allowance = line.city_allowance
				
			#GROSS Calculation
			if line.wage:
				gross_amount = line.wage

			#PF Calculation
			if (line.wage) >= 15000:
				pf_amount = 15000*12/100
			else:
				pf_amount = (line.wage)*12/100

			#ESIC Calculation
			if (line.wage) <=21000:
				esic_amount = (line.wage)*3.25/100

			#Gratuity Calculation
			gratuity_amount = basic_amount*4.81/100

			#Bonus Calculation
			bonus_amount = basic_amount*8.33/100

			#PF Calculation
			if (line.wage) >= 15000:
				pf_amount_emp = 15000*12/100			
			else:
				pf_amount_emp = (line.wage)*12/100			

			#ESI Calculation
			if basic_amount+hra_amount+mobile_conveyance+city_allowance+special_amount <=21000:
				esi_amount = (basic_amount+hra_amount+mobile_conveyance+city_allowance+special_amount)*0.75/100

			#PT Calculation
			if basic_amount+hra_amount+mobile_conveyance+city_allowance+special_amount >=15000:
				pt_amount = 200
			line.proposed_ctc = round((gross_amount + pf_amount + esic_amount + bonus_amount + gratuity_amount +insurance_amount) * 12)


class HrSalaryStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	basic_amount = fields.Float(string="Basic Salary",required=True)
	insurance_amount = fields.Float(string="Insurance",required=True)