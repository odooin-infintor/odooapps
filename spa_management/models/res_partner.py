# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    birthday = fields.Date(string='DOB')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name, args, operator, limit)
        if name:
            domain = list(args or [])
            domain += [
                '|', '|',
                ('name', 'ilike', name),
                ('phone', 'ilike', name),
                ('mobile', 'ilike', name),
            ]
            partners = self.search(domain, limit=limit)
            res += partners.name_get()
            res = list(set(res))
        return res
