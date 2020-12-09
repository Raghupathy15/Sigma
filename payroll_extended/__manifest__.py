{
    'name': "Payroll customisation",
    'description': """
    Module linking the Payslip.
    """,
    'category': 'Hidden',
    'version': '1.0',
    'author': "Kumar",
    'depends': ['base', 'hr_payroll', 'hr_holidays', 'hr', 'hr_leave_calculation', 'hr_employee_updation'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/multi_payslip.xml',
        'views/hr_payslip_views.xml',
        'views/loan_deduction.xml',
    ],
    'auto_install': True,
}
