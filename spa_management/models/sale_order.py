# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    branch_id = fields.Many2one('spa.branch', string="Branch")
    booking_ids = fields.One2many('spa.booking', 'order_id', string="Bookings")
    sale_type = fields.Selection([
        ('normal', 'Normal Sale'),
        ('booking', 'Service Booking'),
        ], string="Sale Type", default="normal")
    coupon_code = fields.Char(string="Coupon Code")
    is_coupon_applied = fields.Boolean(compute="_compute_coupon_status")

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        if 'branch_id' not in res:
            res['branch_id'] = self.env.user.branch_id.id or False
        return res

    @api.depends('coupon_code')
    def _compute_coupon_status(self):
        if self.applied_coupon_ids:
            self.is_coupon_applied = True
        else:
            self.is_coupon_applied = False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.warehouse_id = self.branch_id.warehouse_id or self.env.user._get_default_warehouse_id()

    def action_save_and_close(self):
        self.ensure_one()
        if self._context.get('calendar_booking'):
            return {
                'type': 'ir.actions.client',
                'tag': 'calendar_booking',
            }
        return True

    def action_confirm_booking(self):
        self.ensure_one()
        booking = self.booking_ids[:1]
        if not booking:
            booking = self.env['spa.booking'].browse(self._context.get('booking_id'))

        if self.state not in ['sale', 'done']:
            self.action_confirm()

        pickings = self.mapped('picking_ids')
        for picking in pickings:
            if not picking.state == 'done':
                picking.action_set_quantities_to_reservation()
                picking.button_validate()

        invoice = booking.invoice_id
        if not invoice:
            invoice = self._create_invoices(final=True)
            booking.invoice_id = invoice.id

        if invoice.state not in ['posted']:
            invoice.action_post()

        action = self.env.ref('spa_management.spa_payment_action').sudo().read()[0]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_invoice_id': invoice.id,
            'default_order_id': self.id,
            'default_booking_id': booking.id,
            'hide_payment_line': False,
        }
        if invoice.amount_total == 0.0:
            booking.state = 'done'
            action['context'].update({'hide_payment_line': True})

        return action

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'booking_ids': [(6, 0, self.booking_ids.ids)],
            'branch_id': self.branch_id.id,
        })
        return invoice_vals

    def action_apply_coupon(self):
        self.ensure_one()
        if self.coupon_code:
            ctx = {'active_id': self.id}
            coupon = self.env['sale.coupon.apply.code'].with_context(**ctx).create({
                'coupon_code': self.coupon_code,
            })
            coupon.process_coupon()
            if self._context.get('calendar_booking'):
                return {
                    'type': 'ir.actions.act_window',
                    'views': [[False, 'form']],
                    'name': 'Sale Order',
                    'res_model': 'sale.order',
                    'res_id': self.id,
                    'target': 'new',
                    'nodestroy': True,
                }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    user_id = fields.Many2one('res.users', string="Assign to")
    employee_id = fields.Many2one('hr.employee', string="Assign to")
