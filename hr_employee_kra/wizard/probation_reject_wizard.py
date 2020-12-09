# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime


class ProbationRejectWizard(models.TransientModel):
    _name = 'probation.reject.wizard'
    _description = 'Probation Reject Wizard'

    name = fields.Text('Rejection Remarks')

    @api.multi
    def action_reject_probation(self):
        active_id = self.env.context.get('active_id')
        rec = self.env['kra.probation'].browse(int(active_id))
        for order in rec:
            print(order,'order')
            order.write({'hod_remarks': self.name})
            order.write({'hod_status': 'reject'})
            order.write({'state': 'reject', 'hod_date': datetime.now()})
            template_id = self.env.ref('cron_probation.email_template_probation_creation_rej')
            template_id.send_mail(order.id, force_send=True)
            # Reminder Notification
            hr_reminder = order.env['hr.reminder'].sudo().create({
                'name': 'Probation Evaluation form is rejected for employee',
                'employee_id': order.employee_id.id, 'model_name': 'kra.probation',
                'approver_ids': [(6, 0, order.hr_reminder_approver1_ids.ids)],
                'hr_probation_id': order.id
            })
