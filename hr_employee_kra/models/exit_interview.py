from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class ExitInterviewMaster(models.Model):
    _name = 'exit.interview.master'
    _inherit = ['mail.thread']
    _description = "Exit Interview Master"

    name = fields.Char(string="Name", required=True)
    owner = fields.Many2one('hr.department', string="Owner")
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the induction master without removing it.")
    exit_interview_master_date = fields.Datetime(string='Exit Interview Master',
                                                 default=lambda self: fields.datetime.now(),
                                                 track_visibility='onchange')


class KraExitIntw(models.Model):
    _name = 'kra.exit.intw'
    _description = "Exit Interview"
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.model
    def _default_interview_line(self):
        master = self.env['exit.interview.master']
        vals = []
        master_ids = master.search([])
        for line in master_ids:
            data = {}
            data['name'] = line.name
            data['answer'] = ' '
            vals.append((0, 0, data))
        return vals

    name = fields.Char('Name', copy=False)
    resignation_id = fields.Many2one('hr.resignation', string="Resignation Ref")
    seq_date = fields.Datetime(string="Seq Date", default=lambda self: fields.datetime.now())
    state = fields.Selection([('draft', 'Draft'), ('hr_approve', 'Waiting for employee to acknowledge'),
                              ('emp_acknowledge', 'Waiting for HR to approve'), ('done', 'Done'), ('cancel', 'Cancel')],
                             default='draft', copy=False, string="Status", readonly=False, track_visibility='onchange',
                             track_sequence=2)
    employee_code = fields.Char('Employee ID', related="employee_id.employee_id")
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    help='Department of the employee')
    doc_no = fields.Char('Doc No')
    rev_no = fields.Char('Rev No')
    doc_created_date = fields.Datetime(string="Document Date", default=lambda self: fields.datetime.now())
    rev_date = fields.Date('Rev Date')
    ref = fields.Char('Ref')
    location_work_id = fields.Many2one('work.location', string="Work Location", related="employee_id.location_work_id",
                                       track_visibility='always')
    job_id = fields.Many2one('employee.designation', 'Designation', related="employee_id.designation_id", store=True)
    l1_manager_id = fields.Many2one('hr.employee', string="Approver 1", related="employee_id.lone_manager_id")
    l2_manager_id = fields.Many2one('hr.employee', string="Approver 2", related="employee_id.ltwo_manager_id")
    doj = fields.Date('Date of Joining', related="employee_id.joining_date", required=True)
    relieve_date = fields.Date('Releiving Date', required=True, default=fields.Date.today())
    user_id = fields.Many2one('res.users', string='Related User', index=True, track_visibility='onchange',
                              track_sequence=2, related="employee_id.user_id", store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    interview_line_ids = fields.One2many('exit.interview.line', 'interview_id', default=_default_interview_line)
    is_hr = fields.Boolean('Hr user', compute="compute_hr_user")

    @api.depends('user_id')
    def compute_hr_user(self):
        for rec in self:
            var = self.env.user.has_group('hr_employee_kra.group_kra_hr')
            # print("VAR", var)
            if var:
                rec.is_hr = True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('kra.exit.intw')
        res = super(KraExitIntw, self).create(vals)
        return res

    @api.multi
    def action_submit(self):
        for line in self:
            if self.is_hr:
                line.write({'state': 'hr_approve'})
            else:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))

    @api.multi
    def button_acknowledge(self):
        for line in self:
            if self.env.user.id == self.employee_id.user_id.id:
                line.write({'state': 'emp_acknowledge'})
            else:
                raise UserError(_('You are not a authorized user to perform acknowledgement .')) \

    @ api.multi
    def button_set_to_draft(self):
        for line in self:
            if self.is_hr:
                line.write({'state': 'draft'})
            else:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))

    @api.multi
    def button_interview_done(self):
        for line in self:
            if self.is_hr:
                line.write({'state': 'done'})
            else:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))

    # @api.multi
    # def action_submit(self):
    # 	current_employee = self.env.uid
    # 	is_employee = self.env.user.has_group('hr_employee_kra.group_kra_user')
    # 	for line in self:
    # 		if line.user_id.id != current_employee:
    # 			raise UserError(_('You are not a authorized user to perform actions in this document.'))
    # 		if line.user_id.id == current_employee:
    # 			line.write({'state': 'hr_approve'})

    @api.multi
    def action_approve(self):
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        for line in self:
            if is_hr:
                line.write({'state': 'done'})
            else:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))

    @api.multi
    def action_reject(self):
        is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
        for line in self:
            if is_hr:
                line.write({'state': 'draft'})
            else:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def set_to_draft(self):
        current_employee = self.env.uid
        is_employee = self.env.user.has_group('hr_employee_kra.group_kra_user')
        for line in self:
            if line.user_id.id != current_employee:
                raise UserError(_('You are not a authorized user to perform actions in this document.'))
            if line.user_id.id == current_employee:
                line.write({'state': 'draft'})


class ExitInterviewLine(models.Model):
    _name = 'exit.interview.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    interview_id = fields.Many2one('exit.interview')
    name = fields.Char(string="Description")
    answer = fields.Char(string="", required=False)
