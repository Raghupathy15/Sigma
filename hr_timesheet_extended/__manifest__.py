{
    'name': 'Task Logs Extended',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 23,
    'summary': 'Track employee time on tasks',
    'description': """
This module implements a timesheet system.
==========================================

Each employee can encode and track their time spent on the different projects.

Lots of reporting on time and employee tracking are provided.

It is completely integrated with the cost accounting module. It allows you to set
up a management by affair.
    """,
    'website': 'https://www.odoo.com/page/timesheet-mobile-app',
    'depends': ['hr_timesheet', 'project_extended', 'project_timesheet_holidays'],
    'data': [
        'security/hr_timesheet_security.xml',
        'data/timesheet_cron_data.xml',
        'data/timesheet_mail_templates.xml',
        'wizard/approver_remark_wizard_view.xml',
        'wizard/approve_reject_validation_wizard_view.xml',
        'views/res_users_view.xml',
        'views/hr_timesheet_views.xml',
        'views/cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
