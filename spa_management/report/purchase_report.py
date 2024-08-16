# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    branch_id = fields.Many2one('spa.branch', string="Branch", readonly=True)

    def _select(self):
        select_str = super(PurchaseReport, self)._select()
        select_str += ", po.branch_id as branch_id"
        return select_str

    def _group_by(self):
        group_by_str = super(PurchaseReport, self)._group_by()
        group_by_str += ", po.branch_id"
        return group_by_str
