# -*- coding: utf-8 -*-
{
    'name': "Payroll Employee Leave Calculation",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_holidays','hr_attendance','hr_payroll','hr','resource','hr_contract'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/hr_attendance_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_contract_views.xml',
        'views/resource_calendar_views.xml',
        'views/tds_master_views.xml',
        # 'views/self_declaration_views.xml',
        'views/hr_payslip_leave_views.xml',
        'views/lop_salary_rule.xml',
        'views/menu_holiday_views.xml'
    ],
}