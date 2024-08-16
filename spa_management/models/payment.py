# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    booking_id = fields.Many2one('spa.booking', string="Booking")
    branch_id = fields.Many2one('spa.branch', string="Branch")

    @api.model
    def default_get(self, fields):
        res = super(AccountPayment, self).default_get(fields)
        if 'branch_id' not in res:
            res['branch_id'] = self.env.user.branch_id.id or False
        return res

    def action_post(self):
        self = self.with_context(default_branch_id=self.branch_id)
        res = super(AccountPayment, self).action_post()
        if self.booking_id and self.booking_id.invoice_id.payment_state == 'paid':
            self.booking_id.state = 'done'
