from odoo.http import request
from odoo import models, api, fields
import datetime
from dateutil.relativedelta import relativedelta
import calendar
from calendar import monthrange

class ProjectReportXls(models.AbstractModel):
	_name = 'report.attendance_excel_report.project_xlsx'
	_inherit = 'report.report_xlsx.abstract'

	def generate_xlsx_report(self, workbook, data, lines):
		# To get Active id
		active_id = self.env.context.get('active_id')
		wizard = self.env['wizard.project.report'].browse(int(active_id))
		emp = self.env['hr.employee'].sudo().search([('active','=',True),('company_id','=',self.env.user.company_id.id)])
		att = self.env['hr.attendance'].sudo().search([('logged_date','>=',wizard.from_date),('logged_date','<=',wizard.to_date)],order='logged_date')
	  	# Formats
		worksheet = workbook.add_worksheet("Attendance Report")
		format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
		format4 = workbook.add_format({'font_size': 22})
		format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3','align':'center'})
		format3 = workbook.add_format({'font_size': 10,'align':'center'})
		format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
		format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
		format6 = workbook.add_format({'font_size': 22, 'bg_color': '#FFFFFF'})
		# Heading
		worksheet.write('A1',"S.No", format2)
		worksheet.write('B1',"Employee ID", format2)
		worksheet.write('C1',"Employee Name", format2)
		worksheet.write('D1',"DOJ", format2)
		worksheet.write('E1',"Designation", format2)
		worksheet.write('F1',"Location", format2)
		worksheet.write('G1',"Grade", format2)
		# datas/Values
		s_no = 0
		row = 1
		column = 0
		emp_id = []
		for value in emp:
			if value:
				s_no += 1
				joining_date = datetime.datetime.strptime(str(value.joining_date),'%Y-%m-%d').strftime('%d/%m/%Y')
				worksheet.write(row, column, s_no, format3)
				worksheet.write(row, column+1,value.employee_id, format3)
				emp_id.append(value.employee_id)
				worksheet.write(row, column+2,value.name, format3)
				worksheet.write(row, column+3,joining_date, format3)
				if value.designation_id:
					worksheet.write(row, column+4,value.designation_id.name, format3)
				if value.location_work_id:
					worksheet.write(row, column+5,value.location_work_id.name, format3)
				if value.employee_grade_id:
					worksheet.write(row, column+6,value.employee_grade_id.name, format3)
				row += 1
		# Header Loop
		row_header = 0
		row_body = 1
		column_header = 5
		d1 = wizard.from_date
		d2 = wizard.to_date
		dates_btwn = d1
		
		att_date = []
		while dates_btwn <= d2:
			column_header+=1
			worksheet.write(row_header,column_header+1,str(dates_btwn), format2)
			att_date.append(dates_btwn)
			dates_btwn = dates_btwn + relativedelta(days=1)
		count_list = len(emp_id)
		date_list = len(att_date)
		# To get total days in current month
		# start_dt = fields.Date.today()
		start_dt = wizard.from_date
		days_in_current_month = monthrange(start_dt.year,start_dt.month)[1]
		
		for i in range(0, count_list):
			column_body = 7
			pre = 0
			absent = 0
			holiday = 0
			wo = 0
			leave = 0
			for vals in att:
				if emp_id[i] == vals.employee_id.employee_id:
					pre += vals.present_day_status_onch
					absent += vals.loss_of_pay_onch
					holiday += vals.holiday
					wo += vals.week_off
					leave += vals.leave_days_onch
					for d in range(0, date_list):
						p = date_list
						l = date_list+1
						w = date_list+2
						h = date_list+3
						a = date_list+4
						days_total = date_list+5
						lop = date_list+6
						if att_date[d] == vals.logged_date:
							worksheet.write(row_body+i, column_body+d,vals.regularize_status or '-', format3)
							worksheet.write(row_body+i, column_body+p,pre or '0', format3)
							worksheet.write(row_body+i, column_body+l,leave or '0', format3)
							worksheet.write(row_body+i, column_body+w,wo or '0', format3)
							worksheet.write(row_body+i, column_body+h,holiday or '0', format3)
							worksheet.write(row_body+i, column_body+a,absent or '0', format3)
							worksheet.write(row_body+i, column_body+days_total,days_in_current_month or '0', format3)
							worksheet.write(row_body+i, column_body+lop,(days_in_current_month - absent) or '0', format3)

		worksheet.write(row_header,column_header+2,"No Days Present", format2)
		worksheet.write(row_header,column_header+3,"Total Leave", format2)
		worksheet.write(row_header,column_header+4,"Weekly off", format2)
		worksheet.write(row_header,column_header+5,"Holiday", format2)
		worksheet.write(row_header,column_header+6,"LOP", format2)
		worksheet.write(row_header,column_header+7,"Total Days", format2)
		worksheet.write(row_header,column_header+8,"Days Payable", format2)
		worksheet.write(row_header,column_header+9,"Remarks", format2)