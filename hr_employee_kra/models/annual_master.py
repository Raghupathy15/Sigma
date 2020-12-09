from odoo import api, fields, models

class HrAnnualAppraisals(models.Model):
	_name = "hr.annual.appraisal"
	_inherit = ['mail.thread']
	_description = 'Annual Appraisal Master'

	kra = fields.Char(string='KRA')
	details_kra = fields.Char(string='Details of the KRA')
	timeline = fields.Selection([('quarterly', 'Quarterly'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('as_and_when', 'As & When'),('annualy', 'Annualy'),('daily', 'Daily'),('regular', 'Regular'),('halfyearly', 'Half Yearly'),('na','NA')],
							 string='Timeline')
	weightage = fields.Integer(string='Weightage %')
	max_rating = fields.Integer(string='Max Rating')
	details_of_achievment = fields.Char(string='Details of achievment')
	annual_appraisal_master_date = fields.Datetime(string='Annual Appraisal Master',default=lambda self: fields.datetime.now(),track_visibility='onchange')

class RateCreteria(models.Model):
	_name = "rate.creteria"
	_inherit = ['mail.thread']
	_description = 'Rate Criteria Master'

	rating_creteria = fields.Char(string='Rating criteria')
	eligible_details = fields.Char(string='Eligible Details')
	final_rating = fields.Float(string='Final Rating')
	eligibility_details = fields.Char(string='Eligibility Details')
	rate_criteria_master_date = fields.Datetime(string='Rate Criteria Master',default=lambda self: fields.datetime.now(),track_visibility='onchange')

class TimelineMaster(models.Model):
	_name = "timeline.master"
	_inherit = ['mail.thread']
	_description = 'Timeline Master'

	name = fields.Char(string='Name')
	active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the induction master without removing it.")
	# rate_criteria_master_date = fields.Datetime(string='Rate Criteria Master',default=lambda self: fields.datetime.now(),track_visibility='onchange')
