# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkShift(models.Model):
    _name = "work.shift"
    _description = "Work Shift"

    sequence = fields.Integer()
    week_day = fields.Selection([
        ('0', 'Sunday'),
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ], string="Week Day", default='1')
    shift_from = fields.Float(string="Shift From")
    shift_to = fields.Float(string="Shift To")
    employee_id = fields.Many2one('hr.employee', string="Beautician")
    is_active = fields.Boolean(string="Active", default=True)
