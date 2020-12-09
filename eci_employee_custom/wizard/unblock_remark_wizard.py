# -*- coding: utf-8 -*-
from odoo import fields, models, api


class UnblockRemarkWizard(models.TransientModel):
	_name = 'unblock.remark.wizard'
	_description = 'Unblock Remark Wizard'

	def get_user_id(self):
		return self.env.uid

	name = fields.Text('Unblock Remarks')
	current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.uid) 

	@api.multi
	def action_unblock_remark(self):
		if self._context.get('is_manager'):
			for employee_id in self.env['hr.employee'].browse(self._context.get('employee_id', False)):
				employee_id.write({'manager_remark_unblock': self.name})
				# To get unblocked history
				active_id = self.env.context.get('active_id')
				rec = self.env['hr.employee'].browse(int(active_id))
				detail = self.env['unblocked.details'].search([('unblocked_id','=',active_id)],order="unblocked_id desc",limit=1)
				recent = self.env['unblocked.details'].search([],order="id desc",limit=1)
				if detail:
					detail.create({'unblocked_id':active_id,'reason':self.name,
									'date':self.write_date,'name':recent.name + 1,
									'user_id':self.current_user.id})
				if not detail:
					detail.create({'unblocked_id':active_id,'reason':self.name,
									'date':self.write_date,'name':1,
									'user_id':self.current_user.id})
		elif self._context.get('is_hr'):
			for employee_id in self.env['hr.employee'].browse(self._context.get('employee_id', False)):
				employee_id.write({'hr_remark_unblock': self.name})
				employee_id.user_id.is_blocked = False
				# To get unblocked history
				active_id = self.env.context.get('active_id')
				rec = self.env['hr.employee'].browse(int(active_id))
				detail = self.env['unblocked.details'].search([('unblocked_id','=',active_id)],order="unblocked_id desc",limit=1)
				recent = self.env['unblocked.details'].search([],order="id desc",limit=1)
				if detail:
					detail.create({'unblocked_id':active_id,'reason':self.name,
									'date':self.write_date,'name':recent.name + 1,
									'user_id':self.current_user.id})
				if not detail:
					detail.create({'unblocked_id':active_id,'reason':self.name,
									'date':self.write_date,'name':1,
									'user_id':self.current_user.id})