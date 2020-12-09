# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Holiday Master Customization',
    'version' : '1.1',
	'author' : 'Indglobal digital private limited',
    'summary': 'Adding additional fields in Holiday master',
    'sequence': 1,
    'description': """Inheriting in Holiday Master""",
    'category' : 'Contacts',
    'website': 'https://www.indglobal.com',
    'depends' : ['base','eci_employee_custom'],
    'data': ['views/resource_views.xml',
            'data/resource_cron_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
