# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Website Custom',
    'version' : '1.1',
	'author' : 'Indglobal digital private limited',
    'summary': 'Customization in website',
    'sequence': 1,
    'description': """Inheriting in website""",
    'category' : 'website',
    'website': 'https://www.indglobal.com',
    'depends' : ['base','web'],
    'data': ['views/webclient_templates.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
