import base64
import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from datetime import datetime

class HrEmployee(models.Model):
	_inherit = 'hr.employee'
	
	monthly_permission = fields.Float(string="Monthly Permission")

