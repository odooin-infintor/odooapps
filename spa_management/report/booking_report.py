# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class BookingReport(models.Model):
    _name = "booking.report"
    _description = "Booking Report"
    _auto = False

    booking_id = fields.Many2one('spa.booking', string="Booking", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    branch_id = fields.Many2one('spa.branch', string="Branch", readonly=True)
    date = fields.Date(string="Booking Date", readonly=True)
    state = fields.Selection([
        ('draft', 'Waiting'),
        ('check_in', 'Check In'),
        ('confirm', 'Check Out'),
        ('done', 'Done'),
        ('no_show', "No-Show"),
        ('cancel', 'Cancelled'),
        ], string="Status", readonly=True)
    source = fields.Selection([
        ('direct', 'Direct'),
        ('phone', 'Telephone'),
        ('web', 'Website'),
        ], string="Booking via", readonly=True)
    check_in_time = fields.Datetime(string="Check In Time", readonly=True)
    check_out_time = fields.Datetime(string="Check Out Time", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    product_id = fields.Many2one('product.product', string="Item", readonly=True)
    user_id = fields.Many2one('res.users', string="Beautician", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Beautician", readonly=True)
    from_time = fields.Selection(selection="_selection_time", string="Time From", readonly=True)
    to_time = fields.Selection(selection="_selection_time", string="Time To", readonly=True)

    @api.model
    def _selection_time(self):
        hr_start = 0
        hr_end = 24
        min_start = 0
        min_end = 60
        step = 5    # 5 Mins.
        vals = []
        while hr_start < hr_end:
            time_val = "%.0f:%.0f" % (hr_start, min_start)
            time_disp = "%02.0f:%02.0f" % (hr_start, min_start)
            vals.append((time_val, time_disp))
            min_start += step
            if min_start == min_end:
                min_start = 0
                hr_start += 1
        return vals

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (SELECT %s FROM (%s) GROUP BY %s)
        """ % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
            min(l.id) as id,
            l.booking_id,
            b.branch_id,
            b.partner_id,
            b.date,
            b.state,
            b.source,
            b.check_in_time,
            b.check_out_time,
            b.currency_id,
            l.product_id,
            l.employee_id,
            l.from_time,
            l.to_time
        """
        return select_str

    def _from(self):
        from_str = """
            spa_booking_line l
                JOIN spa_booking b  ON (l.booking_id = b.id)
                JOIN spa_branch  br ON (b.branch_id = br.id)
                JOIN res_partner p  ON (b.partner_id = p.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            l.booking_id,
            b.branch_id,
            b.partner_id,
            l.product_id,
            l.employee_id,
            b.date,
            b.state,
            b.source,
            b.check_in_time,
            b.check_out_time,
            b.currency_id,
            l.from_time,
            l.to_time
        """
        return group_by_str
