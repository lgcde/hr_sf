# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api
from openerp.fields import Datetime
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT

from ..tools.TimeZoneHelper import UTC_Datetime_To_TW_TZ


class Attendance(models.Model):
    _inherit = "hr.attendance"

    location = fields.Selection((("1", "1"),
                                 ("2", "2"),
                                 ("3", "3"),
                                 ("4", "4"),
                                 ("5", "5"),
                                 ("6", "6"),
                                 ("7", "7"),
                                 ("8", "8")), required=True)
    code = fields.Char(related="employee_id.internal_code", readonly=True)

    upload_log_id = fields.Many2one("hr_sf.attendance_upload_Log", string="Upload log")

    morning_start_work_time = fields.Char(readonly=True)
    morning_end_work_time = fields.Char(readonly=True)
    afternoon_start_work_time = fields.Char(readonly=True)
    afternoon_end_work_time = fields.Char(readonly=True)

    late_minutes = fields.Float(compute="_compute_late_minutes", store=True)
    early_minutes = fields.Float(compute="_compute_early_minutes", store=True)
    overtime_hours = fields.Float(compute="_compute_overtime_hours", store=True)

    forget_card = fields.Boolean()

    @api.depends("name", "action")
    @api.multi
    def _compute_late_minutes(self):
        for attendance in self:
            if attendance.action == "sign_in" and attendance.morning_start_work_time:
                dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
                dt_start_work_time = datetime.datetime.strptime(attendance.morning_start_work_time,
                                                                DEFAULT_SERVER_TIME_FORMAT).time()
                if dt_action_time > dt_start_work_time:
                    now = datetime.datetime.now()
                    dt_action_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                                       hour=dt_action_time.hour,
                                                       minute=dt_action_time.minute,
                                                       second=dt_action_time.second)
                    dt_start_work_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                                           hour=dt_start_work_time.hour,
                                                           minute=dt_start_work_time.minute,
                                                           second=dt_start_work_time.second)
                    attendance.late_minutes = (dt_action_time - dt_start_work_time).seconds / 60.0

    @api.depends("name", "action")
    @api.multi
    def _compute_early_minutes(self):
        for attendance in self:
            if attendance.action == "sign_out" and attendance.afternoon_end_work_time:
                dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
                dt_end_work_time = datetime.datetime.strptime(attendance.afternoon_end_work_time,
                                                              DEFAULT_SERVER_TIME_FORMAT).time()
                if dt_action_time < dt_end_work_time:
                    now = datetime.datetime.now()
                    dt_action_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                                       hour=dt_action_time.hour,
                                                       minute=dt_action_time.minute,
                                                       second=dt_action_time.second)
                    dt_end_work_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                                         hour=dt_end_work_time.hour,
                                                         minute=dt_end_work_time.minute,
                                                         second=dt_end_work_time.second)
                    attendance.early_minutes = (dt_end_work_time - dt_action_time).seconds / 60.0

    @api.multi
    def _altern_si_so(self):
        return True

    _constraints = [
        (_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

    @api.multi
    def adjust(self):
        date = fields.Date.today()
        domain = [("name", "=like", "%s%%" % date)]
        records = self.search(domain)
        if not records:
            return True
        employees = records.mapped("employee_id")
        for emp in employees:
            emp_records = records.filtered(lambda r: r.employee_id == emp)
            emp_records.write({"action": "action"})
            emp_records = emp_records.sorted(key=lambda r: r.name)
            if emp_records:
                emp_records[0].action = "sign_in"
                if len(emp_records) > 1:
                    emp_records[-1].action = "sign_out"

        print "yes cron is ok"

    @api.model
    def create(self, vals):
        ConfigParameter = self.env['ir.config_parameter'].sudo()
        morning_start_work_time = ConfigParameter.get_param('morning_start_work_time')
        morning_end_work_time = ConfigParameter.get_param('morning_end_work_time')
        afternoon_start_work_time = ConfigParameter.get_param('afternoon_start_work_time')
        afternoon_end_work_time = ConfigParameter.get_param('afternoon_end_work_time')
        vals["morning_start_work_time"] = morning_start_work_time
        vals["morning_end_work_time"] = morning_end_work_time
        vals["afternoon_start_work_time"] = afternoon_start_work_time
        vals["afternoon_end_work_time"] = afternoon_end_work_time
        return super(Attendance, self).create(vals)

    @api.depends("name", "action")
    @api.multi
    def _compute_overtime_hours(self):
        for attendance in self:
            attendance.overtime_hours = 9.99
