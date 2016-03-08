# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class AdjustAttendanceWizard(models.TransientModel):
    _name = "hr_sf.report_attendance_detail_wizard"

    date_from = fields.Date(default=lambda self: fields.date.today())
    date_to = fields.Date(default=lambda self: fields.date.today())

    employee_ids = fields.Many2many("hr.employee")

    @api.multi
    def action_OK(self):
        self.ensure_one()
        data = dict()
        if all((self.date_from, self.date_to)):
            data["date_from"] = self.date_from
            data["date_to"] = self.date_to
        return self.env['report'].get_action(self, 'hr_sf.report_attendance_detail', data=data)
