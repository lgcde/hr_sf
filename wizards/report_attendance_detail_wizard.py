# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ReportAttendanceDetailWizard(models.TransientModel):
    _name = "hr_sf.report_attendance_detail_wizard"

    @api.multi
    def _get_default_date_from(self):
        dt_now = fields.Date.from_string(fields.Datetime.now())
        return fields.Date.to_string(datetime.date(dt_now.year, dt_now.month, 1))

    date_from = fields.Date(default=_get_default_date_from)
    date_to = fields.Date(default=lambda self: fields.date.today())

    filter_by_employee = fields.Boolean()
    employee_ids = fields.Many2many("hr.employee")

    @api.multi
    def action_OK(self):
        self.ensure_one()
        data = dict()
        if all((self.date_from, self.date_to)):
            data["date_from"] = self.date_from
            data["date_to"] = self.date_to
        data["filter_by_employee"] = self.filter_by_employee
        data["employee_ids"] = self.employee_ids.mapped("id")
        return self.env['report'].get_action(self, 'hr_sf.report_attendance_detail', data=data)
