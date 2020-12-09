# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, date
import time
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.web.controllers.main import clean_action


class Kraappraisal(models.Model):
    _name = 'kra.appraisal'
    _description = 'KRA Appraisal'
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.model
    def _default_appraisal_line(self):
        terms_obj = self.env['hr.annual.appraisal']
        terms = []
        termsids = terms_obj.search([])
        for rec in termsids:
            values = {}
            values['kra'] = rec.kra
            values['details_kra'] = rec.details_kra
            values['timeline_id'] = rec.timeline_id
            values['weightage'] = rec.weightage
            values['max_rating'] = rec.max_rating
            values['details_of_achievment'] = rec.details_of_achievment
            terms.append((0, 0, values))
        return terms

    @api.model
    def _default_rate_creteria_line(self):
        terms_obj = self.env['rate.creteria']
        terms = []
        termsids = terms_obj.search([])
        for rec in termsids:
            values = {}
            values['rating_creteria'] = rec.rating_creteria
            values['eligible_details'] = rec.eligible_details
            values['final_rating'] = rec.final_rating
            values['eligibility_details'] = rec.eligibility_details
            terms.append((0, 0, values))
        return terms

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('kra.appraisal') or '/'
        return super(Kraappraisal, self).create(vals)

    name = fields.Char('Order Reference', required=True, index=True, copy=False, default='New')
    seq_date = fields.Datetime(string="Seq Date", default=lambda self: fields.datetime.now())
    appraisal_date = fields.Date(string="Appraisal Date", default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', string="Employee name", required=True)
    department_id = fields.Many2one('hr.department', 'Department', related="employee_id.department_id")
    doj = fields.Date(string="Date of Joining", related="employee_id.joining_date", required=True)
    location_work_id = fields.Many2one('work.location', string="Work Location", related="employee_id.location_work_id",
                                       track_visibility='always')
    employee_code = fields.Char(string="Employee Code", related="employee_id.employee_id", store=True, readonly=False)
    job_id = fields.Many2one('employee.designation', string="Designation", related="employee_id.designation_id",
                             readonly=False, required=True)
    final_rating = fields.Float('Final Rating')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    state = fields.Selection([('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
                              ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
                              ('done', 'Done')],
                             string="Stage", track_visibility='always', readonly=True, copy=False, default='draft')
    l1_remark = fields.Text(string="Approver 1 Remark")
    l2_remark = fields.Text(string="Approver 2 Remark")
    hod_remark = fields.Text(string="HOD Remark")
    annual_appraisal_ids = fields.One2many('annual.appraisal', 'appraisal_id', 'Annual Appraisal',
                                           default=_default_appraisal_line)
    annual_goals_ids = fields.One2many('annual.goals', 'appraisal_id', 'Annual Goal')
    key_acheivement_ids = fields.One2many('annual.key.acheivement', 'appraisal_id', 'Key and Achievement')
    training_details_ids = fields.One2many('annual.training.details', 'appraisal_id', 'Annual Training')
    overall_ids = fields.One2many('overall.appraisal.line', 'appraisal_id', 'Overall')
    # creteria_ids = fields.One2many('appraisal.creteria.line', 'appraisal_id', 'Appaisal creteria', default=_default_creteria_line)
    rate_creteria_ids = fields.One2many('rate.creteria.line', 'appraisal_id', 'Rate creteria',
                                        default=_default_rate_creteria_line)
    kra_quart_count = fields.Integer(string='# Quarterly', compute="_compute_kra_quart_count")
    lop_count = fields.Integer(string='# Quarterly', compute="_compute_lop_count")
    kra_weight = fields.Char('KRA', default="70%", readonly=True)
    degree_rating = fields.Float('360 degree')
    degree_weight = fields.Char('Degree', default="70%", readonly=True)



    key_weight = fields.Char('Key', default="15%", readonly=True)
    training_weight = fields.Char('Training', default="15%", readonly=True)
    user_id = fields.Many2one('res.users', string='Related User', index=True, track_visibility='onchange',
                              track_sequence=2, related="employee_id.user_id", store=True)
    l1_manager_id = fields.Many2one('hr.employee', string="Approver 1", related="employee_id.lone_manager_id")
    l2_manager_id = fields.Many2one('hr.employee', string="Approver 2", related="employee_id.ltwo_manager_id")
    hod_id = fields.Many2one('hr.employee', string="HOD ID", related="employee_id.hod_id")
    director_id = fields.Many2one('hr.employee', 'Director', related="employee_id.parent_id")
    l1_manager = fields.Many2one('res.users', 'Approver1', related="employee_id.lone_manager_id.user_id")
    l2_manager = fields.Many2one('res.users', 'Approver2', related="employee_id.ltwo_manager_id.user_id")
    director_user_id = fields.Many2one('res.users', 'Director', related="employee_id.parent_id.user_id")
    hod_user_id = fields.Many2one('res.users', 'Hod User Id', related="employee_id.hod_id.user_id")
    emp_sumbit_date = fields.Date(string="Employee Submit Date", track_visibility='onchange')
    approver_1_date = fields.Date(string="Approver1 Approved Date", track_visibility='onchange')
    approver_2_date = fields.Date(string="Approver2 Approved Date", track_visibility='onchange')
    hod_approver_date = fields.Date(string="HOD Approved Date", track_visibility='onchange')
    director_approver_date = fields.Date(string="Director Approved Date", track_visibility='onchange')
    current_year = fields.Integer(string="Current Year", compute="check_year")
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id")

    # get Users for Notification/Reminders
    @api.multi
    @api.depends('employee_id')
    def compute_employee_approver1_id(self):
        employee_rec = self.env['hr.employee'].sudo().search([('id', '=', self.employee_id.id)])
        for rec in employee_rec:
            self.hr_reminder_approver1_ids = rec.lone_manager_id
            self.hr_reminder_approver2_ids = rec.ltwo_manager_id
            self.hr_reminder_hod_ids = rec.hod_id
            self.hr_reminder_director_ids = rec.parent_id
            self.employee_ids = rec

    hr_reminder_approver1_ids = fields.Many2many('hr.employee', string='Noti1 Approver1',
                                                 compute="compute_employee_approver1_id")
    hr_reminder_approver2_ids = fields.Many2many('hr.employee', string='Noti2 Approver2',
                                                 compute="compute_employee_approver1_id")
    hr_reminder_hod_ids = fields.Many2many('hr.employee', string='Noti3 Hod',
                                           compute="compute_employee_approver1_id")
    hr_reminder_director_ids = fields.Many2many('hr.employee', string='Noti4 Director',
                                                compute="compute_employee_approver1_id")
    employee_ids = fields.Many2many('hr.employee', string='Noti5 Employee Ids', compute="compute_employee_approver1_id")

    @api.depends('employee_id', 'l1_manager', 'l2_manager', 'user_id', 'hod_user_id', 'director_user_id')
    def hr_group_access(self):
        current_employee = self.env.uid
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')
        for rec in self:
            var = self.env.user.has_group('hr_employee_kra.group_kra_hr')
            if var:
                rec.is_hr = True
            else:
                rec.is_hr = False
            if rec.l1_manager.id == current_employee and is_approver_1:
                rec.approver_1_check = True
            else:
                rec.approver_1_check = False
            if rec.l2_manager.id == current_employee and is_approver_2:
                rec.approver_2_check = True
            else:
                rec.approver_2_check = False
            if rec.user_id.id == current_employee and is_user:
                rec.user_check = True
            else:
                rec.user_check = False
            if rec.hod_user_id.id == current_employee and is_hod:
                rec.hod_check = True
            else:
                rec.hod_check = False
            if rec.director_user_id.id == current_employee and is_director:
                rec.director_check = True
            else:
                rec.director_check = False
            if rec.employee_id.user_id.id == current_employee and rec.state != 'draft':
                rec.edit_access = True
            else:
                rec.edit_access = False
            if rec.employee_id.user_id.id == current_employee and is_hod:
               rec.emp_hod_check = True
            else:
               rec.emp_hod_check = False

    is_hr = fields.Boolean(string="Is Hr", compute="hr_group_access")
    user_check = fields.Boolean(string="User Check", compute="hr_group_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="hr_group_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="hr_group_access")
    hod_check = fields.Boolean(string="HOD Check", compute="hr_group_access")
    director_check = fields.Boolean(string="Director Check", compute="hr_group_access")
    emp_hod_check = fields.Boolean(string="Emp HOD Check", compute="hr_group_access")
    edit_access = fields.Boolean(string="Edit access", compute="_check_users_access")


    @api.multi
    @api.depends('appraisal_date')
    def check_year(self):
        for line in self:
            present_year = line.appraisal_date
            line.current_year = present_year.year

    @api.multi
    def action_view_link_quart(self):
        self.ensure_one()
        action = self.env.ref('hr_employee_kra.action_kra_quarterly').read()[0]
        kra_list = []
        quart_search = self.env['kra.quarterly'].search(
            [('state', '=', 'done'), ('employee_id', '=', self.employee_id.id)], order='id desc', limit=4)
        for count in quart_search:
            kra_list.append(count.id)
        if len(kra_list) >= 1:
            action['domain'] = [('id', 'in', kra_list)]
            return action

    @api.multi
    def action_view_link_lop(self):
        self.ensure_one()
        action = self.env.ref('hr_leave_calculation.hr_leave_payslip_action').read()[0]
        lop_list = []
        lop_search = self.env['hr.payslip.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('current_year', '=', self.current_year)], order='id desc',
            limit=4)
        for count in lop_search:
            lop_list.append(count.id)
        if len(lop_list) >= 1:
            action['domain'] = [('id', 'in', lop_list)]
            return action

    def _compute_kra_quart_count(self):
        for kra in self:
            kra_list = []
            quart_search = self.env['kra.quarterly'].search(
                [('state', '=', 'done'), ('employee_id', '=', self.employee_id.id)], order='id desc', limit=4)
            for count in quart_search:
                kra_list.append(count.id)
            kra.kra_quart_count = len(kra_list)

    def _compute_lop_count(self):
        for lop in self:
            lop_list = []
            lop_search = self.env['hr.payslip.leave'].search([('employee_id', '=', lop.employee_id.id)],
                                                             order='id desc', limit=4)
            for count in lop_search:
                lop_list.append(count.id)
            lop.lop_count = len(lop_list)

    @api.multi
    @api.depends('annual_appraisal_ids', 'annual_goals_ids', 'key_acheivement_ids', 'training_details_ids',
                 'overall_ids')
    def compute_total(self):
        for val in self:
            total1 = 0
            var1 = 0
            rec1 = 0
            total2 = 0
            var2 = 0
            rec2 = 0
            total3 = 0
            var3 = 0
            rec3 = 0
            total4 = 0
            var4 = 0
            rec4 = 0
            total5 = 0
            var5 = 0
            rec5 = 0
            tot1 = 0
            tot2 = 0
            tot3 = 0
            tot4 = 0
            #annual.apprisal (KRA)
            for appr in val.annual_appraisal_ids:
                if appr.avg_rating:
                    total1 += appr.avg_rating
                    var1 += len(val)
            if total1:
                rec1 = total1 / var1
            # annual.goal (Annual Goals)
            for goal in val.annual_goals_ids:
                if goal.avg_rating:
                    total2 += goal.avg_rating
                    var2 += len(val)
            if total2:
                rec2 = total2 / var2

            #annual.key.acheivement (Key and Achivements)
            for key in val.key_acheivement_ids:
                if key.avg_rating:
                    total3 += key.avg_rating
                    var3 += len(val)
            if total3:
                rec3 = total3 / var3


            #annual.training.details(Annual Training)
            for train in val.training_details_ids:
                if train.avg_rating:
                    total4 += train.avg_rating
                    var4 += len(val)
            if total4:
                rec4 = total4 / var4
            #overall.appraisal.line(OverAll)
            for over in val.overall_ids:
                if over.avg_rating:
                    total5 += over.avg_rating
                    var5 += len(val)
            if total5:
                rec5 = total5 / var5

            #Over all Rating Calculation
            if val.employee_id:
                if rec1 or rec3 or rec4 or rec5:
                    tot1 = rec1 * (70 / 100) * 10
                    tot2 = rec3 * (15 / 100) * 10
                    tot3 = rec4 * (15 / 100) * 10
                    val.kra_rating = tot1
                    val.key_acheive = tot2
                    val.training_details = tot3
                tot = tot1 + tot2 + tot3
                if tot:
                    if tot >= 90.00:
                        val.overall_rating = 5
                    elif tot >= 80.00 and tot < 90.00:
                        val.overall_rating = 4
                    elif tot >= 70.00 and tot < 80.00:
                        val.overall_rating = 3
                    elif tot >= 50.00 and tot < 70.00:
                        val.overall_rating = 2
                    elif tot < 50.00:
                        val.overall_rating = 1

            if val.employee_id:
                if rec1 or rec3 or rec4 or rec5:
                    tot1 = rec1 * (50 / 100) * 10
                    tot2 = rec3 * (20 / 100) * 10
                    tot3 = rec4 * (15 / 100) * 10
                    tot4 = rec5 * (15 / 100) * 10
                    val.hod_kra_rating = tot1
                    val.hod_key_achieve = tot2
                    val.hod_training_details = tot3
                    val.hod_over_all_360_rating = tot4
                tot = tot1 + tot2 + tot3 + tot4
                if tot:
                    if tot >= 90.00:
                        val.hod_overall_rating = 5
                    elif tot >= 80.00 and tot < 90.00:
                        val.hod_overall_rating = 4
                    elif tot >= 70.00 and tot < 80.00:
                        val.hod_overall_rating = 3
                    elif tot >= 50.00 and tot < 70.00:
                        val.hod_overall_rating = 2
                    elif tot < 50.00:
                        val.hod_overall_rating = 1

    kra_rating = fields.Float('KRA Achievement', compute="compute_total")
    key_acheive = fields.Float('Key Achievements', compute="compute_total")
    training_details = fields.Float('Training Details', compute="compute_total")
    overall_rating = fields.Float('Overall Rating (%)', compute="compute_total")
    over_all_360_rating = fields.Float('360 degree appraisal Achievement', compute="compute_total")

    hod_kra_rating = fields.Float('KRA Achievement', compute="compute_total")
    hod_key_achieve = fields.Float('Key Achievements', compute="compute_total")
    hod_training_details = fields.Float('Training Details', compute="compute_total")
    hod_overall_rating = fields.Float('Overall Rating (%)', compute="compute_total")
    hod_over_all_360_rating = fields.Float('360 degree appraisal Achievement', compute="compute_total")


    @api.multi
    def sub_state_employee(self):
        current_employee = self.env.uid
        for line in self:
            if line.user_id.id != current_employee:
                raise UserError(_('You are not a authorized user to Submit this document.'))
            if line.user_id.id == current_employee:
                line.write({'state': 'sub_emp',
                            'emp_sumbit_date': fields.date.today()})
                template_id = self.env.ref('hr_employee_kra.email_template_annual_emp_to_a1')
                template_id.sudo().send_mail(line.id, force_send=True)
                # Reminder Notification
                hr_reminder = line.env['hr.reminder'].sudo().create({
                    'name': 'Employee Submitted Annual assessment',
                    'employee_id': line.employee_id.id, 'model_name': 'kra.appraisal',
                    'approver_ids': [(6, 0, line.hr_reminder_approver1_ids.ids)],
                    'kra_annual_appraisal_id': line.id
                })

    @api.multi
    def sub_state_l1(self):
        current_employee = self.env.uid
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        for line in self:
            if line.l1_manager.id != current_employee:
                raise UserError(_('You are not a authorized user to Submit this document.'))
            if line.l1_manager.id == current_employee and is_approver_1:
                line.write({'state': 'sub_l1',
                            'approver_1_date': fields.date.today()})
                template_id = self.env.ref('hr_employee_kra.email_template_annual_a1_to_a2')
                template_id.sudo().send_mail(line.id, force_send=True)
                # Reminder Notification
                hr_reminder = line.env['hr.reminder'].sudo().create({
                    'name': 'Approver 1 Approved Annual assessment',
                    'employee_id': line.employee_id.lone_manager_id.id, 'model_name': 'kra.appraisal',
                    'approver_ids': [(6, 0, line.hr_reminder_approver2_ids.ids)],
                    'kra_annual_appraisal_id': line.id
                })

    @api.multi
    def sub_state_l2(self):
        current_employee = self.env.uid
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        for line in self:
            if line.l2_manager.id != current_employee:
                raise UserError(_('You are not a authorized user to Submit this document.'))
            if line.l2_manager.id == current_employee and is_approver_2:
                line.write({'state': 'sub_l2',
                            'approver_2_date': fields.date.today()})
                template_id = self.env.ref('hr_employee_kra.email_template_annual_a2_to_hod')
                template_id.sudo().send_mail(line.id, force_send=True)
                # Reminder Notification
                hr_reminder = line.env['hr.reminder'].sudo().create({
                    'name': 'Approver 2 Approved Annual assessment',
                    'employee_id': line.employee_id.ltwo_manager_id.id, 'model_name': 'kra.appraisal',
                    'approver_ids': [(6, 0, line.hr_reminder_hod_ids.ids)],
                    'kra_annual_appraisal_id': line.id
                })

    @api.multi
    def sub_state_hod(self):
        current_employee = self.env.uid
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        for line in self:
            if line.hod_user_id.id != current_employee:
                raise UserError(_('You are not a authorized user to Submit this document.'))
            if line.hod_user_id.id == current_employee and is_hod:
                line.write({'state': 'sub_hod',
                            'hod_approver_date': fields.date.today()})
                template_id = self.env.ref('hr_employee_kra.email_template_annual_hod_to_director')
                template_id.sudo().send_mail(line.id, force_send=True)
                # Reminder Notification
                hr_reminder = line.env['hr.reminder'].sudo().create({
                    'name': 'HOD Approved Annual assessment',
                    'employee_id': line.employee_id.parent_id.id, 'model_name': 'kra.appraisal',
                    'approver_ids': [(6, 0, line.hr_reminder_director_ids.ids)],
                    'kra_annual_appraisal_id': line.id
                })

    @api.multi
    def state_done(self):
        current_employee = self.env.uid
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')
        for line in self:
            if line.director_user_id.id != current_employee:
                raise UserError(_('You are not a authorized user to Validate this document.'))
            if line.director_user_id.id == current_employee and is_director:
                line.write({'state': 'done'})
                # Reminder Notification
                hr_reminder = line.env['hr.reminder'].sudo().create({
                    'name': 'Director Approved Annual assessment',
                    'employee_id': line.employee_id.parent_id.id, 'model_name': 'kra.appraisal',
                    'approver_ids': [(6, 0, line.employee_ids.ids)],
                    'kra_annual_appraisal_id': line.id
                })

    @api.multi
    def reset_draft(self):
        self.write({'state': 'draft'})

    goal_total_weightage = fields.Integer(string="Goal Total Weightage")
    key_total_weightage = fields.Integer(string="Key Total Weightage")

    @api.onchange('annual_goals_ids', 'key_acheivement_ids')
    def total_weightage_onchange(self):
        sum_weightage = 0
        sum_key_weightage = 0
        for rec in self:
            for data in rec.annual_goals_ids:
                sum_weightage += data.weightage
                rec.goal_total_weightage = sum_weightage
            for key_data in rec.key_acheivement_ids:
                sum_key_weightage += key_data.weightage
                rec.key_total_weightage = sum_key_weightage

    @api.constrains('goal_total_weightage', 'key_total_weightage')
    def total_weightage_warning(self):
        if self.goal_total_weightage != 100:
            raise ValidationError(_("Annual Goals over all Weightage should be 100..."))
        if self.key_total_weightage != 100:
            raise ValidationError(_("Key and Achievement over all Weightage should be 100..."))


class AnnualAppraisal(models.Model):
    _name = 'annual.appraisal'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    state = fields.Selection(
        [('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
         ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
         ('sub_dir', 'Done')],
        string="Stage", track_visibility='always', readonly=True, copy=False, related='appraisal_id.state')
    kra = fields.Char('KRA')
    details_kra = fields.Char(string='Details of the KRA')
    timeline_id = fields.Many2one('timeline.master', string="Timeline")
    timeline = fields.Selection(
        [('quarterly', 'Quarterly'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('as_and_when', 'As & When'),
         ('annualy', 'Annualy'), ('daily', 'Daily'), ('regular', 'Regular'), ('halfyearly', 'Half Yearly'),
         ('na', 'NA')],
        string='Timeline')
    weightage = fields.Integer(string='Weightage %')
    max_rating = fields.Integer(string='Max Rating', default=10, readonly=True)
    details_of_achievment = fields.Char(string='Details of achievment')
    employee_rating = fields.Integer('Employee Rating')
    l1 = fields.Integer('Approver 1 Rating')
    l2 = fields.Integer('Approver 2 Rating')
    hod_rating = fields.Integer('HOD Rating')
    employee_id = fields.Many2one('hr.employee', string="Employee name", related="appraisal_id.employee_id")


    @api.multi
    @api.depends('employee_rating', 'l1', 'l2', 'hod_rating')
    def compute_avg(self):
        for vals in self:
            if vals.employee_rating or vals.l1 or vals.l2 or vals.hod_rating:
                avg = 0
                avg = vals.employee_rating + vals.l1 + vals.l2 + vals.hod_rating
                vals.avg_rating = avg / 4

    @api.model
    @api.depends('employee_id')
    def _check_users_access(self):
        current_employee = self.env.uid
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')
        for line in self:
            if line.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1:
                line.approver_1_check = True
            else:
                line.approver_1_check = False
            if line.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2:
                line.approver_2_check = True
            else:
                line.approver_2_check = False
            if line.employee_id.user_id.id == current_employee and is_user:
                line.user_check = True
            else:
                line.user_check = False
            if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
                line.hod_check = True
            else:
                line.hod_check = False
            if line.employee_id.parent_id.user_id.id == current_employee and is_director:
                line.director_check = True
            else:
                line.director_check = False

    avg_rating = fields.Float('Average Rating', compute="compute_avg")
    user_check = fields.Boolean(string="User Check", compute="_check_users_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="_check_users_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="_check_users_access")
    hod_check = fields.Boolean(string="HOD Check", compute="_check_users_access")
    director_check = fields.Boolean(string="Director Check", compute="_check_users_access")

    @api.onchange('employee_rating', 'l1', 'l2', 'hod_rating')
    def _onchange_max_rating(self):
        for rec in self:
            if rec.max_rating < rec.employee_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l1:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l2:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.hod_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))




class AnnualGoals(models.Model):
    _name = 'annual.goals'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    state = fields.Selection(
        [('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
         ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
         ('sub_dir', 'Done')],
        string="Stage", track_visibility='always', readonly=True, copy=False, related='appraisal_id.state')
    goals = fields.Char(string='Goals, additional responsibilities and Initiatives (Minimum 3 points to be captured)')
    details_goal = fields.Char(string='Details of the Goal')
    timeline_id = fields.Many2one('timeline.master', string="Timeline")
    timeline = fields.Selection(
        [('quarterly', 'Quarterly'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('as_and_when', 'As & When'),
         ('annualy', 'Annualy'), ('daily', 'Daily'), ('regular', 'Regular'), ('halfyearly', 'Half Yearly'),
         ('na', 'NA')],
        string='Timeline')
    weightage = fields.Integer(string='Weightage %')
    max_rating = fields.Integer(string='Max Rating', default=10, readonly=True)
    employee_rating = fields.Integer('Employee Rating')
    l1 = fields.Integer('Approver 1 Rating')
    l2 = fields.Integer('Approver 2 Rating')
    hod_rating = fields.Integer('HOD Rating')

    employee_id = fields.Many2one('hr.employee', string="Employee name", related="appraisal_id.employee_id")



    @api.multi
    @api.depends('employee_rating', 'l1', 'l2', 'hod_rating')
    def compute_avg(self):
        for vals in self:
            if vals.employee_rating or vals.l1 or vals.l2 or vals.hod_rating:
                avg = 0
                avg = vals.employee_rating + vals.l1 + vals.l2 + vals.hod_rating
                vals.avg_rating = avg / 4

    @api.model
    @api.depends('employee_id')
    def _check_users_access(self):
        current_employee = self.env.uid
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')
        for line in self:
            if line.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1:
                line.approver_1_check = True
            else:
                line.approver_1_check = False
            if line.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2:
                line.approver_2_check = True
            else:
                line.approver_2_check = False
            if line.employee_id.user_id.id == current_employee and is_user:
                line.user_check = True
            else:
                line.user_check = False
            if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
                line.hod_check = True
            else:
                line.hod_check = False
            if line.employee_id.parent_id.user_id.id == current_employee and is_director:
                line.director_check = True
            else:
                line.director_check = False
            if is_hr:
                line.hr_check = True
            else:
                line.hr_check = False


    avg_rating = fields.Float('Average Rating', compute="compute_avg")
    hr_check = fields.Boolean(string="Is Hr", compute="_check_users_access")
    user_check = fields.Boolean(string="User Check", compute="_check_users_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="_check_users_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="_check_users_access")
    hod_check = fields.Boolean(string="HOD Check", compute="_check_users_access")
    director_check = fields.Boolean(string="Director Check", compute="_check_users_access")



    @api.onchange('employee_rating', 'l1', 'l2', 'hod_rating')
    def _onchange_max_rating(self):
        for rec in self:
            if rec.max_rating < rec.employee_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l1:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l2:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.hod_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))


class KeysAcheivements(models.Model):
    _name = 'annual.key.acheivement'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    state = fields.Selection(
        [('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
         ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
         ('sub_dir', 'Done')],
        string="Stage", track_visibility='always', readonly=True, copy=False, related='appraisal_id.state')
    key_achievements = fields.Char(string='Key Achievements')
    details_goal = fields.Char(string='Details of the Goal')
    weightage = fields.Integer(string='Weightage %')
    max_rating = fields.Integer(string='Max Rating', default=10, readonly=True)
    employee_rating = fields.Integer('Employee Rating')
    l1 = fields.Integer('Approver 1 Rating')
    l2 = fields.Integer('Approver 2 Rating')
    hod_rating = fields.Integer('HOD Rating')
    employee_id = fields.Many2one('hr.employee', string="Employee name", related="appraisal_id.employee_id")


    @api.multi
    @api.depends('employee_rating', 'l1', 'l2', 'hod_rating')
    def compute_avg(self):
        for vals in self:
            if vals.employee_rating or vals.l1 or vals.l2 or vals.hod_rating:
                avg = 0
                avg = vals.employee_rating + vals.l1 + vals.l2 + vals.hod_rating
                vals.avg_rating = avg / 4

    @api.model
    @api.depends('employee_id')
    def _check_users_access(self):
        current_employee = self.env.uid
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')
        for line in self:
            if line.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1:
                line.approver_1_check = True
            else:
                line.approver_1_check = False
            if line.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2:
                line.approver_2_check = True
            else:
                line.approver_2_check = False
            if line.employee_id.user_id.id == current_employee and is_user:
                line.user_check = True
            else:
                line.user_check = False
            if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
                line.hod_check = True
            else:
                line.hod_check = False
            if line.employee_id.parent_id.user_id.id == current_employee and is_director:
                line.director_check = True
            else:
                line.director_check = False
            if is_hr:
                line.hr_check = True
            else:
                line.hr_check = False

    avg_rating = fields.Float('Average Rating', compute="compute_avg")

    hr_check = fields.Boolean(string="Is Hr", compute="_check_users_access")
    user_check = fields.Boolean(string="User Check", compute="_check_users_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="_check_users_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="_check_users_access")
    hod_check = fields.Boolean(string="HOD Check", compute="_check_users_access")
    director_check = fields.Boolean(string="Director Check", compute="_check_users_access")


    @api.onchange('employee_rating', 'l1', 'l2', 'hod_rating')
    def _onchange_max_rating(self):
        for rec in self:
            if rec.max_rating < rec.employee_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l1:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l2:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.hod_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))

class AnnualTrainingDetails(models.Model):
    _name = 'annual.training.details'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    state = fields.Selection(
        [('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
         ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
         ('sub_dir', 'Done')],
        string="Stage", track_visibility='always', readonly=True, copy=False, related='appraisal_id.state')
    training_details = fields.Char(string='Training Details')
    details_goal = fields.Char(string='Details of the Goal')
    timeline_id = fields.Many2one('timeline.master', string="Timeline")
    timeline = fields.Selection(
        [('quarterly', 'Quarterly'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('as_and_when', 'As & When'),
         ('annualy', 'Annualy'), ('daily', 'Daily'), ('regular', 'Regular'), ('halfyearly', 'Half Yearly'),
         ('na', 'NA')],
        string='Timeline')
    weightage = fields.Integer(string='Weightage %')
    max_rating = fields.Integer(string='Max Rating', default=10, readonly=True)
    employee_rating = fields.Integer('Employee Rating')
    l1 = fields.Integer('Approver 1 Rating')
    l2 = fields.Integer('Approver 2 Rating')
    hod_rating = fields.Integer('HOD Rating')
    employee_id = fields.Many2one('hr.employee', string="Employee name", related="appraisal_id.employee_id")

    @api.multi
    @api.depends('employee_rating', 'l1', 'l2', 'hod_rating')
    def compute_avg(self):
        for vals in self:
            if vals.employee_rating or vals.l1 or vals.l2 or vals.hod_rating:
                avg = 0
                avg = vals.employee_rating + vals.l1 + vals.l2 + vals.hod_rating
                vals.avg_rating = avg / 4

    @api.model
    @api.depends('employee_id')
    def _check_users_access(self):
        current_employee = self.env.uid
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')

        for line in self:
            if line.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1:
                line.approver_1_check = True
            else:
                line.approver_1_check = False
            if line.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2:
                line.approver_2_check = True
            else:
                line.approver_2_check = False
            if line.employee_id.user_id.id == current_employee and is_user:
                line.user_check = True
            else:
                line.user_check = False
            if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
                line.hod_check = True
            else:
                line.hod_check = False
            if line.employee_id.parent_id.user_id.id == current_employee and is_director:
                line.director_check = True
            else:
                line.director_check = False
            if is_hr:
                line.hr_check = True
            else:
                line.hr_check = False

    avg_rating = fields.Float('Average Rating', compute="compute_avg")

    hr_check = fields.Boolean(string="Is Hr", compute="_check_users_access")
    user_check = fields.Boolean(string="User Check", compute="_check_users_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="_check_users_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="_check_users_access")
    hod_check = fields.Boolean(string="HOD Check", compute="_check_users_access")
    director_check = fields.Boolean(string="Director Check", compute="_check_users_access")



    @api.onchange('employee_rating', 'l1', 'l2', 'hod_rating')
    def _onchange_max_rating(self):
        for rec in self:
            if rec.max_rating < rec.employee_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l1:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l2:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.hod_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))


class OverallAppraisalLine(models.Model):
    _name = 'overall.appraisal.line'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    state = fields.Selection(
        [('draft', 'Draft'), ('sub_emp', 'Submitted by Employee'), ('sub_l1', 'Submitted by Approver 1'),
         ('sub_l2', 'Submitted by Approver 2'), ('sub_hod', 'Submitted by HOD'),
         ('sub_dir', 'Done')],
        string="Stage", track_visibility='always', readonly=True, copy=False, related='appraisal_id.state')
    overall_appraisal = fields.Char(string='360 Dergree Appraisal Form')
    max_rating = fields.Integer(string='Max Rating', default=10, readonly=True)
    employee_rating = fields.Char('Employee Rating', default="N/A")
    l1 = fields.Integer('HOD 1 Rating')
    l2 = fields.Integer('HOD 2 Rating')
    hod_rating = fields.Integer('HOD Rating', invisible=True)
    employee_id = fields.Many2one('hr.employee', string="Employee name", related="appraisal_id.employee_id")

    @api.multi
    @api.depends('l1', 'l2')
    def compute_avg(self):
        for vals in self:
            if vals.l1 or vals.l2:
                avg = 0
                avg = vals.l1 + vals.l2
                vals.avg_rating = avg / 2

    @api.model
    @api.depends('employee_id')
    def _check_users_access(self):
        current_employee = self.env.uid
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        is_approver_2 = self.env.user.has_group('hr_employee_kra.group_kra_approver_2')
        is_user = self.env.user.has_group('hr_employee_kra.group_kra_user')
        is_hod = self.env.user.has_group('hr_employee_kra.group_kra_hod')
        is_director = self.env.user.has_group('hr_employee_kra.group_kra_director')

        for line in self:
            if line.employee_id.lone_manager_id.user_id.id == current_employee and is_approver_1:
                line.approver_1_check = True
            else:
                line.approver_1_check = False
            if line.employee_id.ltwo_manager_id.user_id.id == current_employee and is_approver_2:
                line.approver_2_check = True
            else:
                line.approver_2_check = False
            if line.employee_id.user_id.id == current_employee and is_user:
                line.user_check = True
            else:
                line.user_check = False
            if line.employee_id.hod_id.user_id.id == current_employee and is_hod:
                line.hod_check = True
            else:
                line.hod_check = False
            if line.employee_id.parent_id.user_id.id == current_employee and is_director:
                line.director_check = True
            else:
                line.director_check = False
            if is_hr:
                line.hr_check = True
            else:
                line.hr_check = False

    avg_rating = fields.Float('Average Rating', compute="compute_avg")

    hr_check = fields.Boolean(string="Is Hr", compute="_check_users_access")
    user_check = fields.Boolean(string="User Check", compute="_check_users_access")
    approver_1_check = fields.Boolean(string="Approver 1 Check", compute="_check_users_access")
    approver_2_check = fields.Boolean(string="Approver 2 Check", compute="_check_users_access")
    hod_check = fields.Boolean(string="HOD Check", compute="_check_users_access")
    director_check = fields.Boolean(string="Director Check", compute="_check_users_access")

    @api.onchange('l1', 'l2', 'hod_rating')
    def _onchange_max_rating(self):
        for rec in self:
            if rec.max_rating < rec.l1:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.l2:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))
            if rec.max_rating < rec.hod_rating:
                raise ValidationError(_("Rating should not be Greater Than Max Rating..."))


class RateCreteriaLine(models.Model):
    _name = 'rate.creteria.line'

    appraisal_id = fields.Many2one('kra.appraisal', 'Annual')
    rating_creteria = fields.Char(string='Rating criteria')
    eligible_details = fields.Char(string='Eligible Details')
    final_rating = fields.Float(string='Final Rating')
    eligibility_details = fields.Char(string='Eligibility Details')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    hike = fields.Float('Hike %')
    total = fields.Monetary('Total', compute="compute_hike", store=True)

    @api.multi
    @api.depends('wage', 'hike')
    def compute_hike(self):
        for vals in self:
            if vals.hike:
                val = vals.wage * vals.hike
                vals.total = val / 100 + vals.wage
