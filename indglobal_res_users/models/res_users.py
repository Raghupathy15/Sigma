from odoo import fields, models
from odoo import api, fields, models, tools, _
from datetime import datetime

class ResUsers(models.Model):
	_inherit = 'res.users'

	blocked_date = fields.Date("Blocked Date")
	img = fields.Text("Employee Master Image pass to Res Users")



class ResUsers(models.Model):
	_inherit = 'hr.employee'


	@api.onchange('image')
	def _onchange_res_image(self):
		current_employee = self.env.uid
		is_hr = self.env.user.has_group('hr_employee_kra.group_kra_hr')
		is_admin_setting = self.env.user.has_group('base.group_user')
		users = self.env['res.users'].sudo().search([('id', '=', self.user_id.id)], limit=1)
		if users and self.image:
			img_str = str(self.image)
			users.write({'img':img_str})
		if (self.user_id.id == current_employee or is_hr or is_admin_setting) and self.image:
			self.edit_img_access = True
		else:
			self.edit_img_access = False
		if (self.user_id.id == current_employee or is_hr or is_admin_setting) and self.image == False and users.image:
			self.remove_img_access = True
		else:
			self.remove_img_access = False

	edit_img_access = fields.Boolean(string="Image Edit access", default=False)
	remove_img_access = fields.Boolean(string="Image Edit access", default=False)

	def res_image_write(self):
		users_master = self.env['res.users'].sudo().search([('id', '=', self.user_id.id)], limit=1)
		if self.image and users_master.img:
			users_master.image = users_master.img
			self.edit_img_access = False
		if self.image == False:
			users_master.image = False
			users_master.img  = False
			self.remove_img_access = False