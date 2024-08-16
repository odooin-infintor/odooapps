# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    branch_id = fields.Many2one('spa.branch', string="Branch")

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        if 'branch_id' not in res:
            res['branch_id'] = self.env.user.branch_id.id or False
        return res

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals['branch_id'] = self.branch_id.id
        return invoice_vals
