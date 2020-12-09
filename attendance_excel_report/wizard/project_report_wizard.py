from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import calendar

class ProjectReportButton(models.TransientModel):
    _name = 'wizard.project.report'

    from_date = fields.Date('From Date',required=True)
    to_date = fields.Date('To Date',required=True)

    @api.onchange('from_date')
    def _onchange_to_date(self):
        if self.from_date:
            month_date = date(self.from_date.year, int(self.from_date.month), 1)
            self.from_date = month_date.replace(day = 1)
            self.to_date = month_date.replace(day = calendar.monthrange(month_date.year, month_date.month)[1])
            nxt_mnth = self.from_date + relativedelta(months=1)
            end_date = nxt_mnth - relativedelta(days=1)
            self.update({'to_date': end_date})
            today = datetime.today()
			# if self.to_date and self.to_date.month == today.month and self.to_date.year == today.year:
			# 	self.to_date = fields.Date.today() - relativedelta(days=1)
            if self.to_date > fields.Date.today():
                self.to_date = fields.Date.today() - relativedelta(days=1)

    @api.multi
    @api.constrains('from_date','to_date')
    def constrains(self):
        if self.to_date >= fields.Date.today():
            raise ValidationError('"To date" should be less than current date !..')

    @api.multi
    def print_project_report_xls(self):
        for rec in self.env['hr.attendance'].search([('logged_date','>=',self.from_date),('logged_date','<=',self.to_date)]):
            if rec:
                if rec.present_day_status_onch != rec.present_day_status or rec.loss_of_pay_onch != rec.loss_of_pay or rec.leave_days_onch != rec.leave_days or rec.holiday != rec.holiday_onch or rec.week_off != rec.week_off_onch or rec.holiday_status_onch_id != rec.holiday_status_id or rec.regularize_status != rec.attendance_status:
                    rec.present_day_status_onch = rec.present_day_status
                    rec.loss_of_pay_onch = rec.loss_of_pay
                    rec.leave_days_onch = rec.leave_days
                    rec.holiday = rec.holiday_onch
                    rec.week_off = rec.week_off_onch
                    rec.regularize_status = rec.attendance_status
        data = {
            'ids': self.ids,
            'model': self._name,
            # 'record': record.id,
        }
        return self.env.ref('attendance_excel_report.project_xlsx').report_action(self, data=data)
