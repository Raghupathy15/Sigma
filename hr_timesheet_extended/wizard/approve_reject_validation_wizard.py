# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ApproverValidationWizard(models.TransientModel):
    _name = 'approver.validation.wizard'
    _description = 'Approver Validation Wizard'

    name = fields.Text('Approver Validation')

    @api.multi
    def action_approver_validation(self):
        if self._context.get('is_draft'):
            for timesheet_id in self.env['account.analytic.line'].search([('employee_id','=',self._context.get('employee_id')),('date','=',self._context.get('date'))]):
            	if timesheet_id.state == 'draft':
            		timesheet_id.write({'state': 'pending'})