# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SpaBranch(models.Model):
    _name = "spa.branch"
    _description = "Spa Branch"

    @api.model
    def _default_warehouse_id(self):
        return self.env.user._get_default_warehouse_id()

    name = fields.Char(string="Name")
    user_ids = fields.One2many('res.users', 'branch_id', string="Beauticians")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", default=_default_warehouse_id)
    resource_line_ids = fields.One2many('spa.resource.line', 'branch_id', string="Resources")
    company_id = fields.Many2one('res.company', string="Company",default= lambda self:self.env.company)
