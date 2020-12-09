# -*- coding: utf-8 -*-
{
    'name': "KRA",

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
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['hr_leave_calculation','hr','payslip_report','mail','eci_employee_custom','hr_contract','hr_resignation'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/annual_master.xml',
        'views/full_and_final_settlement_views.xml',
        # 'views/hr_applicant_views.xml',
        'views/exit_clearance_views.xml',
        'views/exit_interview_views.xml',
        'views/hr_induction_views.xml',
        'views/hr_kra_views.xml',
        'views/hr_kra_revision_views.xml',
        'views/quaterly_review_views.xml',
        'views/menu_customization_views.xml',
        'views/annual_performance_views.xml',
        'views/probation_views.xml',
        'views/self_declaration_views.xml',
        'views/hr_employee_views.xml',
        'wizard/probation_reject_wizard_views.xml',
        'wizard/induction_remarks_views.xml',
        'wizard/kra_remarks_views.xml',
        'wizard/quarterly_remarks_views.xml',
        'data/ir_sequence_data.xml',
        'data/email_template.xml',
        'data/quarterly_cron.xml',
		'data/annual_cron.xml',
        'data/annual_email_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
