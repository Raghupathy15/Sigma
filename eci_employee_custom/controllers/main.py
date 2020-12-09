import simplejson as json
from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class APIController(http.Controller):
    @http.route(['/api/device'], type='http', auth="public", methods=['POST'], csrf=False)
    def check_device_id(self, user_id=None, device_id=None, **post):
        emp_id = request.env['hr.employee'].sudo().search([('user_id','=',int(user_id))])
        # emp_id = request.env['hr.employee'].sudo().browse(int(employee_id))
        if emp_id.device_id == device_id:
            _logger.info("\n\n\n\n emp_id call")
            success_msg = {'success': True}
            return json.dumps(success_msg)
        else:
            error_msg = {'error': False}
            return json.dumps(error_msg)
