
{
    'name': 'Attendance Excel Report XLS',
    'version': '12.0.1.1.0',
    "category": "Project",
    'author': 'Indglobal Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Indglobal Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'summary': """Advanced XLS Reports for Attendance""",
    'depends': ['base', 'hr_attendance', 'report_xlsx'],
    'license': 'AGPL-3',
    'data': [
            'wizard/project_report_wizard_view.xml',
            'views/project_report.xml'
             ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
