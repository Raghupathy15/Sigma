# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrEmployeeKraBatch(models.TransientModel):
    _name = 'hr.employee.kra.batch'
    _description = 'KRA Creation'

    name = fields.Char(string="Name")
    month = fields.Selection([('1', 'January'),
                                  ('2', 'Febraury'),
                                  ('3', 'March'),
                                  ('4', 'April'),
                                  ('5', 'May'),
                                  ('6', 'June'),
                                  ('7', 'July'),
                                  ('8', 'August'),
                                  ('9', 'September'),
                                  ('10', 'October'),
                                  ('11', 'November'),
                                  ('12', 'December')],
                                  string="Month")
    quarter = fields.Selection([('1', 'First Quarter'),
                                  ('2', 'Second Quarter'),
                                  ('3', 'Third Quarter'),
                                  ('4', 'Fourth Quarter')],
                                  string="KRA Quarter")
    year = fields.Selection([('2019','2019')],string = "Year")

    job_id = fields.Many2one('hr.job',string = "Job Position")

    employee_ids = fields.Many2many('hr.employee','employee_id',string="Employee")

    @api.multi
    @api.onchange('job_id')
    def fetch_employee_ids(self):
    	for line in self:
    		line.employee_ids = False
    		if line.job_id:
    			employee = self.env['hr.employee'].search([('job_id','=',line.job_id.id)])
    			if employee:
    				for emp in employee:
    					line.employee_ids = emp.ids


    @api.multi
    def create_kra(self):
    	for line in self:
    		if line.job_id:
    			# hr_kra = self.env['hr.kra']
    			vals= {}
    			for emp in line.employee_ids:
    				vals ={
    				'employee_id': emp.id,
    				'year':line.year,
    				'month':line.month,
    				'quarter':line.quarter,
    				'state':'draft',
    				'name':emp.name
    				}
    				hr_kra=self.env['hr.kra'].create(vals)

    				#fetch the question based on the job position
    				job = self.env['hr.employee.kra'].search([('id','=',line.job_id.hr_employee_kra_id.id)])
    				if job:
    					for kra in job:
    						hr_kra_question = self.env['hr.kra.question']
    						val_lines ={}
    						for kra_lines in kra.question_ids:
    							val_lines = {
    							'name':kra_lines.name,
    							'description':kra_lines.description,
    							'hint':kra_lines.hint.id,
    							'time_line':kra_lines.time_line,
    							'question_id':hr_kra.id
    							}
    							hr_kra_question.create(val_lines)




    				


	    		# kra = self.env['hr.employee.kra'].search([('id','=',line.job_id.hr_employee_kra_id.id)])
	    		# if kra:
	    		# 	for line in kra:


