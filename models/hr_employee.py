# _*_ coding: utf-8 _*_
import datetime
from collections import defaultdict
from openerp import models, fields, api
from openerp.fields import Date
from openerp.fields import Datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..tools.TimeZoneHelper import UTC_String_From_TW_TZ
from ..tools.TimeZoneHelper import UTC_String_To_TW_TZ
from ..tools.TimeZoneHelper import UTC_Datetime_From_TW_TZ
from ..tools.TimeZoneHelper import UTC_Datetime_To_TW_TZ


class Employee(models.Model):
    _inherit = "hr.employee"

    card_code = fields.Char(help="考勤卡卡号。")
    internal_code = fields.Char()
    responsibility = fields.Boolean(help="用于标识这个员工是不是责任制。")

    holidays_ids = fields.One2many("hr.holidays", "employee_id")

    # @api.multi
    # def get_attendance(self, date=None, location=None):
    #     self.ensure_one()
    #     HRAttendance = self.env["hr.attendance"].sudo()
    #     domain = []
    #     if date:
    #         domain.append(("name", "=like", "%s%%" % date))
    #     if location:
    #         domain.append(("location", "=", location))
    #
    #     records = HRAttendance.search(domain)
    #     return records

    @api.multi
    def get_holiday_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        querying_day = date
        if isinstance(date, datetime.date):
            querying_day = Date.to_string(date)

        leaves = defaultdict(lambda: datetime.timedelta())  # _time = datetime.timedelta()

        for holiday in self.holidays_ids:
            if not holiday.date_from or not holiday.date_to:
                continue

            if not all((holiday.morning_start_work_time,
                        holiday.morning_end_work_time,
                        holiday.afternoon_start_work_time,
                        holiday.afternoon_end_work_time)):
                return None

            dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

            dt_holiday_from = Datetime.from_string(holiday.date_from) + datetime.timedelta(hours=8)
            dt_holiday_to = Datetime.from_string(holiday.date_to) + datetime.timedelta(hours=8)
            # deal with morning first
            dt_cal_start = max(dt_the_day_morning_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

            dt_cal_end = min(dt_the_day_morning_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)

            if dt_cal_end > dt_cal_start:
                leaves[holiday.holiday_status_id.name] += dt_cal_end - dt_cal_start

            # then deal with afternoon first
            dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)

            dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

            if dt_cal_end > dt_cal_start:
                leaves[holiday.holiday_status_id.name] += dt_cal_end - dt_cal_start

        return leaves

    @api.multi
    def get_start_work_time_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_in_attendance(date)

        return UTC_Datetime_To_TW_TZ(attendance.name) if attendance else None

    @api.multi
    def get_work_duration_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        sign_in_attendance = self.get_sign_in_attendance(date)
        sign_out_attendance = self.get_sign_out_attendance(date)
        if sign_in_attendance and sign_out_attendance:
            dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_in_attendance.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_in_attendance.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_out_attendance.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_out_attendance.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

            dt_sign_in_time = Datetime.from_string(sign_in_attendance.name) + datetime.timedelta(hours=8)
            dt_sign_out_time = Datetime.from_string(sign_out_attendance.name) + datetime.timedelta(hours=8)

            # morning first
            dt_cal_start = max(dt_the_day_morning_start_work_time, dt_sign_in_time)
            dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

            # dt_cal_end = min(dt_the_day_morning_end_work_time, dt_sign_out_time)
            # dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)
            dt_cal_end = dt_the_day_morning_end_work_time
            work_duration = datetime.timedelta()
            if dt_cal_end > dt_cal_start:
                work_duration += dt_cal_end - dt_cal_start

            # then deal with afternoon
            # dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_sign_out_time)
            # dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)
            dt_cal_start = dt_the_day_afternoon_start_work_time

            dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_sign_out_time)
            dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

            if dt_cal_end > dt_cal_start:
                work_duration += dt_cal_end - dt_cal_start

            return work_duration.seconds / 3600.0

    @api.multi
    def get_sign_in_attendance(self, date):
        self.ensure_one()

        Attendance = self.env["hr.attendance"].sudo()

        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("action", "=", "sign_in")])
        if attendances:
            attendance = attendances[0] if len(attendances) > 1 else attendances
            return attendance
        else:
            return None

    @api.multi
    def get_sign_out_attendance(self, date):
        self.ensure_one()

        Attendance = self.env["hr.attendance"].sudo()

        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("action", "=", "sign_out")])
        if attendances:
            attendance = attendances[0] if len(attendances) > 1 else attendances
            return attendance
        else:
            return None

    @api.multi
    def get_end_work_time_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_out_attendance(date)

        return UTC_Datetime_To_TW_TZ(attendance.name) if attendance else None

    @api.multi
    def get_early_minutes_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_out_attendance(date)
        return attendance.early_minutes if attendance else None

    @api.multi
    def get_late_minutes_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_in_attendance(date)
        return attendance.late_minutes if attendance else None

    @api.multi
    def get_forget_card_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        Attendance = self.env["hr.attendance"].sudo()
        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("forget_card", "=", True)])
        return len(attendances) if attendances else 0

    @api.multi
    def get_overtime_hours_on(self, date_from=None, date_to=None):
        self.ensure_one()
        if not all((date_from, date_to)):
            return None

        if self.responsibility:
            return 0

        Overtime = self.env["hr_sf.overtime"].sudo()

        date_from = "%s %s" % (date_from, "0:0:0")
        date_from = UTC_String_From_TW_TZ(date_from)

        date_to = "%s %s" % (date_to, "23:59:59")
        date_to = UTC_String_From_TW_TZ(date_to)

        overtimes = Overtime.search([("date_from", ">=", date_from),
                                     ("date_to", "<=", date_to),
                                     ("employee_ids", "in", self.id),
                                     ("state", "=", "confirmed")])

        # TODO 这里还要检查有没有打卡记录
        return sum(o.duration for o in overtimes) if overtimes else 0
