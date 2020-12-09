# -*- coding: utf-8 -*-
{
    'license': 'LGPL-3',
    'name': "Document Management System",
    'summary': "online document management",
    'author': "Indglobal digital private limited",
    'website': "https://indglobal.in/",
    'support': 'Indglobal digital private limited',
    'category': 'Document Management',
    'version': '1.0',
    'depends': ['mail'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/document.xml',
    ],
    'images': ['static/description/module_icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}