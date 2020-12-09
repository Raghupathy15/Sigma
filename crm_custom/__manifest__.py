{
'name' : 'CRM Custom',
'version' : '12.0',
'author' : 'Indglobal',
'website' : 'http://www.indglobal.in',
'category' : 'Tools',
'depends' : ['base', 'crm','indglobal_city_master', 'hr'],
'description' : 'CRM Custom',
'data' : [
		'security/ir.model.access.csv',
		'data/ir_sequence.xml',
		'views/crm_lead.xml',
		'views/cron.xml'

	],
'installable': True
}