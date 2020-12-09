# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

YEARS = []
for year in range(int(date.today().strftime('%Y')) - 4 , int(date.today().strftime('%Y')) + 1):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
          ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
          ('11', 'November'), ('12', 'December')]

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    encash_leave = fields.Float(string="Encash Leave", compute='compute_salary_encash_leave')
    encash_amt = fields.Float(string="Encash Amount", compute='compute_salary_encash_leave')
    processing_month = fields.Selection(PERIOD, string="Required Month", default=date.today().strftime('%m'))

    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_salary_encash_leave(self):

        leave_to_encash = self.env['leave.encash'].search([
                        ('employee_id', '=', self.employee_id.id),
                        ('state', '=', 'approved'),
                        ])
        for encash in leave_to_encash:
            if encash.processing_month == '01' or encash.processing_month == '02':
                if line.processing_month == '02' or line.processing_month == '03':
                    self.encash_leave += encash.remaining_leave
        if self.struct_id.basic_amount and self.days_in_current_month:
            self.encash_amt = float(self.struct_id.basic_amount/float(self.days_in_current_month))*self.encash_leave


    # @api.multi
    # def action_payslip_done(self):
    #     res = super(hr_payslip, self).action_payslip_done()
    #     if self.state == 'done':
    #         if line.processing_month == '02' or line.processing_month == '03':
    #             leave_to_encash = self.env['leave.encash'].search([
    #                             ('employee_id', '=', self.employee_id.id),
    #                             ('state', '=', 'approved'),
    #                             ])
    #             for encash in leave_to_encash:
    #                     encash.state = 'paid'
    #                     encash.payslip_id = self.id


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _cron_create_encashment(self):
        current_year = current_month = current_day= 0
        current_year = date.today().strftime('%Y')
        current_month = date.today().strftime('%m')
        current_day = date.today().strftime('%d')
        print('Current Year',current_year)
        print('Current Month',current_month)
        print('Current Day',current_day)
        if int(current_month) == 1 and int(current_day)<=7:
            employee_list = self.env['hr.employee']
            for line in employee_list:
                template_id = self.env.ref('leave_custom_salary_rule.email_template_leave_encashment')
                template_id.send_mail(self.id, force_send=True)
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4