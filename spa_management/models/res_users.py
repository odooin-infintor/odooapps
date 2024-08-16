# -*- coding: utf-8 -*-

from odoo import api, fields, models
import requests
import math
import random

class ResUsers(models.Model):
    _inherit = "res.users"

    is_spa_user = fields.Boolean(string="Spa User", default=True)
    branch_id = fields.Many2one('spa.branch', string="Branch")
    is_beautician = fields.Boolean(string="Beautician", default=False)
    product_ids = fields.Many2many('product.template', string="Services")


    @api.model
    def default_get(self, fields):
        res = super(ResUsers, self).default_get(fields)
        if 'branch_id' not in res:
            branch = self.env.ref('spa_management.main_branch')
            res['branch_id'] = branch and branch.id or False
        return res

    def action_load(self):
        self.ensure_one()
        products = self.env['product.template'].search([('type', '=', 'service')])
        self.product_ids |= products

    def check_availablity(self, from_date, to_date):
        self.ensure_one()
        res = True
        if from_date and to_date:
            block_bookings = self.block_booking_ids.filtered(
                lambda r: (r.from_date <= from_date < r.to_date) or (r.from_date < to_date <= r.to_date))
            res = not bool(block_bookings)
        return res
