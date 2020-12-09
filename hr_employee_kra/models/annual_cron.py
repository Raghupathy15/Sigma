# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class AnnualBlockCron(models.Model):
    _name = 'annual.block.cron'

    # *****Cron For Annual *******#
    @api.multi
    def annual_employee_block(self):
        today = date.today()
        domain_five = today + relativedelta(days=-5)
        domain_seven = today + relativedelta(weeks=-1)
        for users_master in self.env['res.users'].sudo().search([('active', '=', True), ('is_blocked', '=', False)]):
            for annual_master in users_master.env['kra.appraisal'].sudo().search([]):
                if annual_master.seq_date:
                    seq_create_date = annual_master.seq_date.date() or False
                if annual_master.emp_sumbit_date:
                    emp_sub_date = annual_master.emp_sumbit_date or False
                if annual_master.approver_1_date:
                    app1_sub_date = annual_master.approver_1_date or False
                if annual_master.approver_2_date:
                    app2_sub_date = annual_master.approver_2_date or False
                if annual_master.hod_approver_date:
                    hod_sub_date = annual_master.hod_approver_date or False

                # Self assessment by employee(within 5days)#
                if annual_master.state == 'draft' and annual_master.seq_date and annual_master.employee_id.user_id.id == users_master.id and seq_create_date <= domain_five:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': annual_master.employee_id.id,
                         'employee_id': annual_master.employee_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Annual Form Not Submitted To Approver1'})
                #L1 Manager Review (within 7days)#
                if annual_master.state == 'sub_emp' and annual_master.emp_sumbit_date and annual_master.employee_id.lone_manager_id.user_id.id == users_master.id and emp_sub_date <= domain_seven:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': annual_master.employee_id.lone_manager_id.id,
                         'employee_id': annual_master.employee_id.lone_manager_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Annual Form Not Submitted To Approver2'})
                # L2 Manager Review(within 7days) #
                if annual_master.state == 'sub_l1' and annual_master.approver_1_date and annual_master.employee_id.ltwo_manager_id.user_id.id == users_master.id and app1_sub_date <= domain_seven:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': annual_master.employee_id.ltwo_manager_id.id,
                         'employee_id': annual_master.employee_id.ltwo_manager_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Annual Form Not Submitted To HOD'})
                # HOD Review(within 7days) ##
                if annual_master.state == 'sub_l2' and annual_master.approver_2_date and annual_master.employee_id.hod_id.user_id.id == users_master.id and app2_sub_date <= domain_seven:
                    users_master.write({'is_blocked': True})
                    employee_blocked_details = self.env['blocked.details'].sudo().create(
                        {'blocked_id': annual_master.employee_id.hod_id.id,
                         'employee_id': annual_master.employee_id.hod_id.id,
                         'date': fields.Date.today(),
                         'blocked_date': fields.Date.today(),
                         'reason': 'Annual Form Not Submitted To Director'})