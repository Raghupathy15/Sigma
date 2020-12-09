# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
from dateutil.relativedelta import relativedelta


GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeContractName(models.Model):
    """This class is to add emergency contact table"""

    _name = 'hr.emergency.contact'
    _description = 'HR Emergency Contact'

    number = fields.Char(string='Number', help='Contact Number')
    relation = fields.Char(string='Contact', help='Relation with employee')
    employee_obj = fields.Many2one('hr.employee', invisible=1)


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'


    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
                                  invisible=1)

    member_name = fields.Char(string='Name')
    relation = fields.Selection([('father', 'Father'),
                                 ('mother', 'Mother'),
                                 ('daughter', 'Daughter'),
                                 ('son', 'Son'),
                                 ('wife', 'Wife')], string='Relationship', help='Relation with employee')
    member_contact = fields.Char(string='Contact No')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True,track_visibility='onchange')
    # joining_date = fields.Date(string='Joining Date')
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID',track_visibility='onchange')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID',track_visibility='onchange')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id',track_visibility='onchange')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport',track_visibility='onchange')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information',track_visibility='onchange')
    emergency_contacts = fields.One2many('hr.emergency.contact', 'employee_obj', string='Emergency Contact',track_visibility='onchange')
    father_name = fields.Char("Father's Name",track_visibility='onchange')
    father_dob = fields.Date("Father's DOB",track_visibility='onchange')
    mother_name = fields.Char("Mother's Name",track_visibility='onchange')
    mother_dob = fields.Date("Mother's DOB",track_visibility='onchange')
    current_address = fields.Text(string='Current Address', required=False,track_visibility='onchange')
    permanent_address = fields.Text(string='Permanent Address', required=False,track_visibility='onchange')
    marital_status = fields.Selection([('single','Single'),('married','Married')],string='Marrital status',track_visibility='onchange')
    spouse_name = fields.Char("Spouse's Name",track_visibility='onchange')
    spouse_dob = fields.Date("Spouse's DOB",track_visibility='onchange')
    child1_name = fields.Char("Child 1 Name",track_visibility='onchange')
    child1_dob = fields.Date("Child 1 DOB",track_visibility='onchange')
    child2_name = fields.Char("Child 2 Name",track_visibility='onchange')
    child2_dob = fields.Date("Child 2 DOB",track_visibility='onchange')
    
class AccountBlocking(models.Model):
    _name = 'account.blocking'
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee',string="Employee Name")
    blocked_date = fields.Date("Blocked Date")
    remark = fields.Text("Remarks")
    active = fields.Boolean("Active",default=True)

    def _cron_check_date(self):
        import datetime
        curr_date = fields.Date.today()
        acc = self.env['account.blocking'].search([('active','=',True)])
        if acc:
            for rec in acc:
                old_date = curr_date + datetime.timedelta(days=-7)
                if rec.blocked_date < old_date:
                    rec.unlink()

class CronHistory(models.Model):
    _name = 'cron.history'
    _order = "id desc"

    user_id = fields.Many2one('res.users',string="User")
    date = fields.Date("Date")
    remark = fields.Text("Cron")
    active = fields.Boolean("Active",default=True)

    # def _cron_check_date(self):
    #     import datetime
    #     curr_date = fields.Date.today()
    #     acc = self.env['cron.history'].search([('active','=',True)])
    #     if acc:
    #         for rec in acc:
    #             old_date = curr_date + datetime.timedelta(months=-1)
    #             if rec.blocked_date < old_date:
    #                 rec.unlink()