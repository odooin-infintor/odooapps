# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SpaResource(models.Model):
    _name = "spa.resource"
    _description = "Resources"

    name = fields.Char(string="Name")
    note = fields.Text(string="Note")
    line_ids = fields.One2many('spa.resource.line', 'resource_id', string="Occupancy")
    active = fields.Boolean(default=True)

    def check_availablity(self, from_date, to_date, branch_id):
        res = []
        if from_date and to_date and branch_id:
            Booking = self.env['spa.booking.line']
            for resource in self:
                bookings = Booking.search([
                    ('booking_id.branch_id', '=', branch_id),
                    ('product_id.resource_ids.id', '=', resource.id),
                    ('booking_id.state', 'in', ['draft', 'check_in', 'confirm']),
                    '|', '|',
                    '&', ('from_date', '>=', from_date), ('from_date', '<', to_date),
                    '&', ('to_date', '>', from_date), ('to_date', '<=', to_date),
                    '&', ('from_date', '<', from_date), ('to_date', '>', to_date),
                    ])
                booking_count = len(bookings)
                max_occupancy = sum(resource.line_ids.filtered(lambda r: r.branch_id.id == branch_id).mapped('occupancy'))
                if max_occupancy and booking_count >= max_occupancy:
                    res.append(resource.name)
        return res


class SpaResourceLine(models.Model):
    _name = "spa.resource.line"
    _description = "Resource Occupancy"
    _rec_name = "resource_id"

    resource_id = fields.Many2one('spa.resource', string="Resource")
    branch_id = fields.Many2one('spa.branch', string="Branch")
    occupancy = fields.Integer(string="Max. Occupancy", default=1)
