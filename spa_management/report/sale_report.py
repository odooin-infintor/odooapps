# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    branch_id = fields.Many2one('spa.branch', string="Branch", readonly=True)
    beautician_id = fields.Many2one('hr.employee', string="Beautician", readonly=True)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_date = fields.Datetime(related="order_id.date_order", string="Order Date", store=True)
    branch_id = fields.Many2one(related="order_id.branch_id", string="Branch", store=True)
    order_type = fields.Selection(related="order_id.sale_type", string="Order Type", store=True)
