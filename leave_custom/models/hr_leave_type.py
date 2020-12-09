# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round

class HolidaysType(models.Model):
	_inherit = 'hr.leave.type'

	allocated_days = fields.Integer('Allocated Days')

	@api.multi
	def name_get(self):
		if not self._context.get('employee_id'):
			# leave counts is based on employee_id, would be inaccurate if not based on correct employee
			return super(HolidaysType, self).name_get()
		res = []
		for record in self:
			name = record.name
			if record.allocation_type != 'no':
				name = "%(name)s (%(count)s)" % {
					'name': name,
					'count': _('%g') % (
						float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0
					)
				}
			res.append((record.id, name))
		return res
