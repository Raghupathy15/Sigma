
{
    'name': 'Open HRMS Resignation',
    'version': '12.0.2.0.0',
    'summary': 'Handle the resignation process of the employee',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': ['hr_employee_updation', 'mail', 'eci_employee_custom'],
    'category': 'Generic Modules/Human Resources',
    'maintainer': 'Cybrosys Techno Solutions',
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizards/cancel_remark_view.xml',
        'data/resign_employee.xml',
        'data/resignation_mail_templates.xml',
        'views/hr_employee.xml',
        'views/resignation_view.xml',
        'views/approved_resignation.xml',
        'views/resignation_sequence.xml',
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
}

