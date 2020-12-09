# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details. 

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime



class HrKra(models.Model):
    _inherit = 'hr.kra'

    revision_no = fields.Char(string='KRA Revision Number', size=32, readonly=True, states={'draft': [('readonly', False)], 'done': [('readonly', False)]})
    revision_count = fields.Integer(string='Revision Count')
    rev_line = fields.One2many('hr.kra.revision', 'rev_id', string='Revisions')

    _sql_constraints = [
        ('name_uniq', 'unique(revision_no, company_id)', 'Revision Number must be unique!'),
    ]

    @api.multi
    def create_revisions(self):
        current_employee = self.env.uid
        is_approver_1 = self.env.user.has_group('hr_employee_kra.group_kra_approver_1')
        for lines in self:
            if lines.reporting_manager_user_id.id != current_employee:
                raise UserError(_('You are not a authorized user to revise this document.'))
            if lines.reporting_manager_user_id.id == current_employee and is_approver_1:
                rev_obj = self.env['hr.kra.revision']
                rev_line_obj = self.env['hr.kra.revision.line']
                kra_id = self[0]
                if kra_id.kra_line_ids:
                    revision_count = kra_id.revision_count + 1
                    revision_no = str(kra_id.name) + '- R' + str(revision_count)
                    rev_id = rev_obj.create({
                        'name': revision_no,
                        'employee_id':kra_id.employee_id.id,
                        'objective':kra_id.objective,
                        'reason_l2_manager':kra_id.reason_l2_manager,
                        'reason_by_employee':kra_id.reason_by_employee,
                        'rev_id': kra_id.id
                        })
                else:
                    raise UserError(('There is no line item to revise.'))
                for line in kra_id.kra_line_ids:
                    vals = {
                        'revision_id': rev_id.id,
                        'name': line.name,
                        'details': line.details,
                        'time_line': line.time_line,
                        # 'employee_id':line.employee_id.id,
                        # 'company_id':line.company_id.id,
                        'target': line.target,
                    }
                    rev_line_obj.create(vals)
                self.write({'revision_no': revision_no,'reason_l2_manager':'','reason_by_employee':'', 'revision_count': revision_count,'state':'revised','kra_created_date':fields.date.today()})
        return rev_line_obj


class HrKraRevision(models.Model):
    _name = 'hr.kra.revision'
    _inherit = ['mail.thread']

    name = fields.Char('Revision No.', size=32, readonly=True,track_visibility='onchange')
    rev_id = fields.Many2one('hr.kra', 'Order Reference',track_visibility='onchange')
    revision_line = fields.One2many('hr.kra.revision.line', 'revision_id', 'Revision Lines',copy=True)

    employee_id = fields.Many2one('hr.employee',string="Employee Name",store=True,track_visibility='onchange')
    employee_code = fields.Char(string="Employee Id",related="employee_id.code",store=True)
    date_of_joining = fields.Date(string="Date of Joining",related="employee_id.joining_date",store=True)
    reporting_manager = fields.Many2one('hr.employee',string="Reporting Manager",related="employee_id.parent_id",store=True,track_visibility='onchange')
    department = fields.Many2one('hr.department',string="Department",related="employee_id.department_id",store=True)
    work_location = fields.Many2one('work.location',string="Work Location",related="employee_id.location_work_id",store=True)
    state = fields.Selection([('draft','Draft'),('l2_approval','KRA Created'),('resubmit','Resubmit'),('resubmitted','Resubmitted'),('reject','Disagree'),('employee','Approved by Approver 2'),('done','Done')],string="State",default='draft')
    # reason_l1_manager = fields.Text('Reason For L1')
    reason_l2_manager = fields.Text('Approver 2 Remarks',track_visibility='onchange')
    reason_by_employee = fields.Text('Employee Remarks',track_visibility='onchange')
    
    kra_created_date = fields.Date(string="Doc Date",store=True,default=lambda self:fields.date.today())
    reporting_manager_user_id = fields.Many2one('res.users',string="Reporting Manager User Id",related="employee_id.parent_id.user_id",store=True)
    document_created_by = fields.Many2one('res.users', string='Created User', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.uid ,store=True)
    user_id = fields.Many2one('res.users', string='Related User', index=True, track_visibility='onchange', track_sequence=2, related="employee_id.user_id")
    objective = fields.Text(string="Objective")
    total_weightage = fields.Float(string="Total Weightage")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('hr.kra.revision'))
    


    @api.multi
    def apply_revisions(self):
        revision_id = self[0]
        kra_line_obj = self.env['hr.kra.line']
        for l in revision_id.rev_id.kra_line_ids:
            l.unlink()
        for x in revision_id.revision_line:
            vals = {
                'name': x.name,
                'details': x.details,
                'time_line': x.time_line,
                'target': x.target,
                'employee_id':x.employee_id.id,
                'company_id':x.company_id.id,
                'kra_id': x.revision_id.rev_id.id,
            }
            kra_line_obj.create(vals)
        self.env['hr.kra'].update({'revision_no': revision_id.name})
        return  {
                'type': 'ir.actions.client',
                'tag' : 'reload'
               }

class HrKraRevisionLine(models.Model):
    _name = 'hr.kra.revision.line'

    revision_id = fields.Many2one('hr.kra.revision', string='Revision Ref.', required=True, ondelete='cascade', readonly=True)

    name = fields.Char(string="Key Result Area")
    details = fields.Char(string="Details of Key Result Area")
    time_line = fields.Selection([('daily', 'Daily'),
                                  ('weekly', 'Weekly'),
                                  ('monthly', 'Monthly'),
                                  ('as&when', 'As & When'),
                                  ('annually', 'Annually'),
                                  ('quarterly', 'quarterly'),
                                  ('regular', 'Regular')],
                                  string="Timeline")
    target = fields.Integer(string="Target (%)")
    employee_id = fields.Many2one('hr.employee',string="Employee Name",related="revision_id.employee_id",store=True)
    company_id = fields.Many2one('res.company', 'Company', related="revision_id.company_id",store=True)