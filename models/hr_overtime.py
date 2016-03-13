# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.fields import Datetime


class Overtime(models.Model):
    _name = "hr_sf.overtime"

    employee_ids = fields.Many2many("hr.employee")
    date_from = fields.Datetime(requried=True)
    date_to = fields.Datetime(requried=True)
    duration = fields.Float(help="加班时数，以小时为单位。")  # compute="_compute_duration", , store=True
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed")], default="draft")

    @api.constrains("date_from", "date_to")
    @api.multi
    def _constrains_date(self):
        self.ensure_one()
        if self.date_from >= self.date_to:
            raise ValidationError(_("date to must later then date from"))
            # @api.depends("date_from", "date_to")
            # @api.multi
            # def _compute_duration(self):
            #     for overtime in self:
            #         if all((overtime.date_from, overtime.date_to)):
            #             dt_date_from = Datetime.from_string(overtime.date_from)
            #             dt_date_to = Datetime.from_string(overtime.date_to)
            #             overtime.duration = (dt_date_to - dt_date_from).seconds / 3600.0

    @api.constrains("date_from", "date_to")
    @api.multi
    def _constrains_date(self):
        self.ensure_one()
        if self.duration <= 0:
            raise ValidationError(_("duration must greater then 0"))
