# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    booking_ids = fields.One2many('spa.booking', 'invoice_id', string="Bookings")
    branch_id = fields.Many2one('spa.branch', string="Branch")

    @api.model
    def default_get(self, fields):
        res = super(AccountMove, self).default_get(fields)
        if 'branch_id' not in res:
            res['branch_id'] = self.env.user.branch_id.id or False
        return res

    def action_invoice_register_payment(self):
        ctx = {
            'default_booking_id': self.booking_ids[:1].id,
            'default_branch_id': self.branch_id.id,
        }
        self = self.with_context(**ctx)
        return super(AccountMove, self).action_invoice_register_payment()


class CustomAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    employee_id = fields.Many2one(
        related='sale_line_ids.employee_id',
        string="Beautician",
        store=True,
        readonly=True
    )
