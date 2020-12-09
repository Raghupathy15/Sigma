# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class QuarterlyCron(models.Model):
    _name = 'quarterly.cron'

    # *****Cron For quarterly *******#
    @api.multi
    def quarterly_employee_block(self):
        today = date.today()
        domain = today + relativedelta(weeks=-1)
        for users_master in self.env['res.users'].sudo().search([('active', '=', True), ('is_blocked', '=', False)]):
            for quaterly_master in users_master.env['kra.quarterly'].sudo().search([]):
                if quaterly_master.employee_date:
                    emp_sub_date = quaterly_master.employee_date.date() or False
                if quaterly_master.approver_1_date:
                    app1_sub_date = quaterly_master.approver_1_date.date() or False
                if quaterly_master.approver_2_date:
                    app2_sub_date = quaterly_master.approver_2_date.date() or False
                if quaterly_master.resumbitted_app_2_date:
                    resumbitted_date = quaterly_master.resumbitted_app_2_date.date() or False
                if quaterly_master.revised_emp_date:
                    emp_accept_date = quaterly_master.revised_emp_date.date() or False
                # Self assessment by employee under employee login - he has to fill in the ratings within 7days and submit to L1#
                if quaterly_master.state == 'draft' and quaterly_master.date and quaterly_master.employee_id.user_id.id == users_master.id and quaterly_master.date <= domain:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': quaterly_master.employee_id.id,
                         'employee_id': quaterly_master.employee_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Quarterly Form Not Submitted To Approver1'})
                # template_id = self.env.ref('cron_probation.email_template_kra_creation')
                # template_id.send_mail(quaterly_master.id, force_send=True)
                # L1 Manager Review- update the rating within 7days and submit to L2#
                # if quaterly_master.employee_id.lone_manager_id.user_id.id == users_master.id:
                if quaterly_master.state == 'app1' and quaterly_master.employee_date and quaterly_master.employee_id.lone_manager_id.user_id.id == users_master.id and quaterly_master.resumbitted_app_2_date == False and emp_sub_date <= domain:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': quaterly_master.employee_id.lone_manager_id.id,
                         'employee_id': quaterly_master.employee_id.lone_manager_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Quarterly Form Not Submitted To Approver2'})
                # L2 Manager Review- update the rating within 7days and submit #
                if quaterly_master.state == 'app2' and quaterly_master.approver_1_date and quaterly_master.employee_id.ltwo_manager_id.user_id.id == users_master.id and quaterly_master.resumbitted_app_2_date == False and app1_sub_date <= domain:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': quaterly_master.employee_id.ltwo_manager_id.id,
                         'employee_id': quaterly_master.employee_id.ltwo_manager_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Quarterly Form Not Approved'})
                # below 70% of Form Rerevised L1 Manager Review- update the rating within 7days and submit to L2#
                # Post L2 review, if overall rating is below 70%. The form has to go back to L1 Manager to update PIP(Performance Improvement Plan)
                if quaterly_master.state == 'reject' and quaterly_master.employee_id.lone_manager_id.user_id.id == users_master.id and quaterly_master.resumbitted_app_2_date and resumbitted_date <= domain:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': quaterly_master.employee_id.lone_manager_id.id,
                         'employee_id': quaterly_master.employee_id.lone_manager_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Re-revised Quarterly Form Not Submitted To Employee'})
                # below 70% of Form Rerevised L1 Manager Review- update the rating within 7days and submit to L2#
                # Post L2 review, if overall rating is below 70%. The form has to go back to L1 Manager to update PIP(Performance Improvement Plan)
                if quaterly_master.state == 'l1_resub' and quaterly_master.employee_id.user_id.id == users_master.id and quaterly_master.revised_emp_date and emp_accept_date <= domain:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': quaterly_master.employee_id.id,
                         'employee_id': quaterly_master.employee_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Revised Quarterly Form Not Accepted'})
