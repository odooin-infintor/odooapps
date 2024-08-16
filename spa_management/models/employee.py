# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    branch_id = fields.Many2one('spa.branch', string="Branch")
    is_beautician = fields.Boolean(string="Beautician", default=False)
    product_ids = fields.Many2many('product.template', string="Services")
    work_shift_ids = fields.One2many('work.shift', 'employee_id', string="Work Shift")
    spa_booking_ids = fields.One2many('spa.booking', 'employee_id')
    overlap_timing = fields.Boolean(string='Overlap  Timings')
    work_permit_name = fields.Char(string="work_permit_name")

    def action_load(self):
        self.ensure_one()
        products = self.env['product.template'].search([('type', '=', 'service')])
        self.product_ids |= products

    def check_availablity(self, from_date, to_date,current_line,booking_name,overlap_timing):
        self.ensure_one()

        res = True
        # TODO: add a config for booking overlaping
        if from_date and to_date:
            domain = [('employee_id','=',self.id),('booking_id.state','not in',['cancel','no_show'])]
            if current_line:
                domain += [('id', '!=', current_line)]
            booking_lines = self.env['spa.booking.line'].search(domain)
            if self.overlap_timing or overlap_timing:
                booking_lines = False
            if booking_lines:
                block_bookings = booking_lines.filtered(lambda r: ((r.from_date <= from_date < r.to_date) or (r.from_date < to_date <= r.to_date) or (from_date <= r.from_date < to_date) or (from_date < r.to_date <= to_date)))
                res = not bool(block_bookings)
        return res

class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    branch_id = fields.Many2one('spa.branch', string="Branch")
    is_beautician = fields.Boolean(string="Beautician", default=False)
    overlap_timing = fields.Boolean(string='Overlap  Timings')
