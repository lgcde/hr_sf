# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
from openerp.fields import Datetime


class Overtime(models.Model):
    _name = "hr_sf.overtime"
    _rec_name = "date_from"
    employee_ids = fields.Many2many("hr.employee")
    date_from = fields.Datetime(requried=True)
    date_to = fields.Datetime(requried=True)
    duration = fields.Float(help="加班时数，以小时为单位。")  # compute="_compute_duration", , store=True
    state = fields.Selection([("draft", "Draft"),
                              ("confirmed", "Confirmed"),
                              ("approved", "Approved")], default="draft")

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

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.state = "confirmed"

    @api.multi
    def action_approve(self):
        self.ensure_one()
        self.state = "approved"

    @api.multi
    def unlink(self):
        for overtime in self:
            if overtime.state == "approved":
                raise Warning(_("Can not delete approved overtimes!"))
