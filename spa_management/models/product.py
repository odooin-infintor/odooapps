# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    duration_hrs = fields.Integer(string="Duration Hours", default=1)
    duration_min = fields.Integer(string="Duration minutes", default=0)
    user_ids = fields.Many2many('res.users', string="Beauticians")
    employee_ids = fields.Many2many('hr.employee', string="Beauticians")
    resource_ids = fields.Many2many('spa.resource', string="Required Resources")
    branch_ids = fields.Many2many('spa.branch', string="Branches",default=[[6,0,[1]]])


class ProductProduct(models.Model):
    _inherit = "product.product"

    booking_line_ids = fields.One2many('spa.booking.line', 'product_id', string="Bookings")

    def check_resource_availablity(self, from_date, to_date, branch_id):
        self.ensure_one()
        return self.resource_ids.check_availablity(from_date, to_date, branch_id)
