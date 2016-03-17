# _*_ coding: utf-8 _*_
import datetime
import string
from openerp import models, api, _
from openerp.fields import Date
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ReportAttendanceDetail(models.AbstractModel):
    _name = "report.hr_sf.report_attendance_detail"

    @api.multi
    def render_html(self, data=None):
        date_from = data.get("date_from", None)
        date_to = data.get("date_to", None)

        filter_by_employee = data.get("filter_by_employee", None)
        employee_ids = data.get("employee_ids", None)

        docargs = dict()
        docargs["emp_attendances"] = self.get_attendance_detail(date_from, date_to, filter_by_employee, employee_ids)
        docargs["date_from"] = date_from
        docargs["date_to"] = date_to
        return self.env['report'].render('hr_sf.report_attendance_detail', values=docargs)

    def get_attendance_detail(self, date_from=None, date_to=None, filter_by_employee=None, employee_ids=None):
        CAL_START_TIME = datetime.datetime.now()
        print "开始计算出勤明细表:", CAL_START_TIME
        if any((date_from, date_to)) and not all((date_from, date_to)):
            return "miss date_from or date_to"

        if not date_from and not date_to:
            now = datetime.datetime.now()
            date_from = datetime.datetime(now.year, now.month, 1)
            date_to = datetime.datetime(date_from.year, date_from.month + 1, 1)
        elif date_from and date_to:
            date_from = Date.from_string(date_from)
            date_to = Date.from_string(date_to)

        Employee = self.env["hr.employee"].sudo()

        emp_attendances_values = []

        employee_search_domain = []
        if filter_by_employee and employee_ids:
            employee_search_domain.append(("id", "in", employee_ids))
        all_employees = Employee.search(employee_search_domain)

        for emp in all_employees:
            dt = date_from
            emp_lines = list()
            while dt <= date_to:
                dt_str = Date.to_string(dt)

                overtime_hours = emp.get_overtime_hours_on(date_from=dt_str, date_to=dt_str)
                if dt.weekday() in (5, 6) and (emp.responsibility or not overtime_hours):
                    dt += datetime.timedelta(days=1)
                    continue

                line = dict()
                line['name'] = emp.name
                line['emp_dep'] = emp.department_id.name
                line['emp_code'] = emp.internal_code
                line['date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)  # + " %A" Date.to_string(dt)

                start_work_time = emp.get_start_work_time_on(dt_str)
                line["start_work_time"] = start_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
                    if start_work_time else None

                end_work_time = emp.get_end_work_time_on(dt_str)
                line["end_work_time"] = end_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
                    if end_work_time else None

                late_minutes = emp.get_late_minutes_on(dt_str)
                line["late_minutes"] = round(late_minutes, 2) if late_minutes else None

                early_minutes = emp.get_early_minutes_on(dt_str)
                line["early_minutes"] = round(early_minutes, 2) if early_minutes else None

                work_duration = emp.get_work_duration_on(dt_str)
                line["work_duration"] = round(work_duration, 2) if work_duration else None

                line["overtime_hours"] = round(overtime_hours, 2)

                leaves = emp.get_holiday_on(dt_str)
                all_leaves = list()
                for l in leaves.values():
                    all_leaves.extend(l)
                line["holiday_total"] = round(sum(l[2].seconds / 3600.0 for l in all_leaves),2)

                absent_for_summary = []
                absent = emp.get_absent_on(dt_str)
                if absent:
                    absent_for_summary.append(_("absent"))
                line["summary"] = string.join(leaves.keys() + absent_for_summary, ",")
                line["forget_card"] = emp.get_forget_card_on(dt_str)

                emp_attendances_values.append(line)
                emp_lines.append(line)
                dt += datetime.timedelta(days=1)
            emp_total_line = dict()
            emp_total_line["name"] = None
            emp_total_line['emp_dep'] = None
            emp_total_line['emp_code'] = None
            emp_total_line['date'] = '小计'
            emp_total_line['end_work_time'] = None
            emp_total_line['start_work_time'] = None
            emp_total_line['late_minutes'] = sum(l["late_minutes"] or 0 for l in emp_lines)
            emp_total_line['early_minutes'] = sum(l["early_minutes"] or 0 for l in emp_lines)
            emp_total_line["work_duration"] = sum(l["work_duration"] or 0 for l in emp_lines)
            emp_total_line["late_minutes"] = sum(l["late_minutes"] or 0 for l in emp_lines)

            emp_total_line["overtime_hours"] = sum(l["overtime_hours"] or 0 for l in emp_lines)
            emp_total_line["holiday_total"] = sum(l["holiday_total"] or 0 for l in emp_lines)
            emp_total_line["summary"] = string.join(l["summary"] for l in emp_lines)
            emp_total_line["forget_card"] = sum(l["forget_card"] or 0 for l in emp_lines)
            emp_attendances_values.append(emp_total_line)
        CAL_END_TIME = datetime.datetime.now()
        print "结束时间:", CAL_END_TIME
        print "耗时:", CAL_END_TIME - CAL_START_TIME
        return emp_attendances_values
