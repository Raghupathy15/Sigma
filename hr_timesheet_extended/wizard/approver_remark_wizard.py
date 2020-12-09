# -*- coding: utf-8 -*-
from odoo import fields, models, api


# class ApproverRemarkWizard(models.TransientModel):
#     _name = 'approver.remark.wizard'
#     _description = 'Approver Remark Wizard'

#     name = fields.Text('Approver Remarks')

#     @api.multi
#     def action_approver_remark(self):
#         if self._context.get('is_approve'):
#             for timesheet_id in self.env['account.analytic.line'].search([('employee_id','=',self._context.get('employee_id')),('date','=',self._context.get('date'))]):
#                 timesheet_id.write({'approver_remarks': self.name or '', 'state': 'approved'})

    # @api.multi
#     def action_approver_remark(self):
#         if self._context.get('is_approve'):
#             # timesheet_id = self.env['account.analytic.line'].search([('employee_id','=',self._context.get('employee_id')),('date','=',self._context.get('date'))])
#             # print ('BBBBBB', timesheet_id, timesheet_id.employee_id)
#             for timesheet_id in self.env['account.analytic.line'].browse(self._context.get('active_ids', [('employee_id','=',self._context.get('employee_id')),('date','=',self._context.get('date'))])):

#                 # if line.employee_id == self._context.get('employee_id') and line.date == self._context.get('date'):
#                 print ('AAAAAAAAAAAA', timesheet_id, timesheet_id.employee_id)
#                 stop
#                 timesheet_id.write({'approver_remarks': self.name or '', 'state': 'approved'})                
    


class ApproverRejectWizard(models.TransientModel):
    _name = 'approver.reject.wizard'
    _description = 'Approver Reject Wizard'

    name = fields.Text('Approver Remarks')

    @api.multi
    def action_approver_reject(self):
        if self._context.get('is_reject'):
            for timesheet_id in self.env['account.analytic.line'].search([('employee_id','=',self._context.get('employee_id')),('date','=',self._context.get('date'))]):
                if timesheet_id.state == 'pending':
                    timesheet_id.write({'approver_remarks': self.name or '','state': 'rejected'})