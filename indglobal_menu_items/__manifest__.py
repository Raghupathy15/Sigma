{
    'name': 'Indglobal - Menu Items',
    'version': '12.0.1.0.0',
    'summary': 'Menu items',
    'description': """Menu items""",
    'category': 'Tools',
    'author': 'Indglobal',
    'depends': ['hr_holidays','hr_timesheet','hr_attendance','base','hr_employee_kra', 'resource', 'base', 'web', 'auth_signup'],
    'data': [

        'security/menu_group_view.xml',
        'security/ir.model.access.csv',
        'views/menu_item_views.xml',
        'views/login_view.xml',
        'views/hr_attendance.xml',

    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
