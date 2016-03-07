# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.fields import Datetime


class Holiday(models.Model):
    _inherit = "hr.holidays"

    leave_duration = fields.Char(compute="_compute_leave_duration", store=True)

    morning_start_work_time = fields.Char(readonly=True)
    morning_end_work_time = fields.Char(readonly=True)
    afternoon_start_work_time = fields.Char(readonly=True)
    afternoon_end_work_time = fields.Char(readonly=True)

    @api.depends("date_from", "date_to")
    @api.multi
    def _compute_leave_duration(self):
        for holiday in self:
            if all(dt_date_from,dt_date_to):
                dt_date_from = Datetime.from_string(holiday.date_from)
                dt_date_to = Datetime.from_string(holiday.date_to)
                delta = dt_date_to - dt_date_from

                holiday.leave_duration = _("%ddays%dhours%dminutes") % (
                delta.days, delta.seconds / 3600, (delta.seconds % 3600) / 60)

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
        return super(Holiday, self).create(vals)
