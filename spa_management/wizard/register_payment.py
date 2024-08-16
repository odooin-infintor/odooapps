# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SpaPayment(models.TransientModel):
    _name = "spa.payment"
    _description = "Spa Payments"

    booking_id = fields.Many2one('spa.booking', string="Booking")
    partner_id = fields.Many2one('res.partner', string="Customer")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    payment_line_ids = fields.One2many('spa.payment.line', 'payment_id', string="Payment Lines")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    amount_invoice = fields.Monetary(related="invoice_id.amount_total", string="Invoiced Amount")
    amount_total = fields.Monetary(compute="_compute_amount", string="Total Amount")
    amount_residual = fields.Monetary(compute="_compute_amount", string="Balance Amount")
    order_id = fields.Many2one('sale.order', string="Sale Order")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('post', 'Post'),
        ('done', 'Done'),
        ], string="Status", default="draft")
    amount_wallet = fields.Monetary(compute="_compute_amount", string="Wallet Amount")
    use_wallet = fields.Boolean(default=False)

    @api.depends('payment_line_ids.amount', 'use_wallet', 'amount_invoice')
    def _compute_amount(self):
        for payment in self:
            payment.amount_total = sum(payment.payment_line_ids.filtered(lambda p: not p.paid).mapped('amount'))
            amount_residual = payment.invoice_id.amount_residual
            if self.use_wallet:
                self.amount_wallet = min(amount_residual)
                amount_residual -= self.amount_wallet
            payment.amount_residual = amount_residual - payment.amount_total


    def process_wallet_payments(self):
        if self.use_wallet and self.amount_wallet:
            if self.invoice_id.state != 'draft':
                self.invoice_id.button_draft()
            amount = self.amount_wallet * -1
            self.invoice_id.add_wallet_payment_line(amount=amount)
        elif self.amount_residual < 0:
            if self.invoice_id.state != 'draft':
                self.invoice_id.button_draft()
            amount = abs(self.amount_residual)
            self.invoice_id.add_wallet_payment_line(amount=amount)
        return True

    def action_post(self):
        self.ensure_one()
        ctx = {
            'active_id': self.invoice_id.id,
            'active_ids': self.invoice_id.ids,
            'active_model': 'account.move',
        }

        self.process_wallet_payments()
        if self.invoice_id.state != 'posted':
            self.invoice_id.action_post()

        Payment = self.env['account.payment.register']
        for line in self.payment_line_ids.filtered(lambda r: r.journal_id.type in ['bank', 'cash']):
            Payment.with_context(ctx).create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.partner_id.id,
                'payment_date': self.date,
                'journal_id': line.journal_id.id,
                'amount': line.amount,
                'communication'   : self.invoice_id.name,
                'payment_method_line_id': line.journal_id.inbound_payment_method_line_ids[:1].id,
            }).action_create_payments()
            acc_payment=self.env['account.payment'].search([('reconciled_invoice_ids.name','=',self.invoice_id.name),('date','=',self.date)],limit=1)
            acc_payment.write({'branch_id':self.invoice_id.branch_id.id,
                               'booking_id':self.booking_id.id})
            line.paid = True

        services = self.booking_id.booking_line_ids.filtered(lambda line: line.product_type == 'service')
        service_count = len(services)

        if self.booking_id and self.invoice_id.payment_state == 'paid':
            self.booking_id.state = 'done'

        self.state = 'post'

        return  {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'spa.payment',
            'res_id': self.id,
            'context': self.env.context,
            'target': 'new',
        }

    def action_cancel(self):
        if self._context.get('calendar_booking'):
            return {
                'type': 'ir.actions.client',
                'tag': 'calendar_booking',
            }
        return True

    def action_print_receipt(self):
        if self.state == 'post':
            self.state = 'done'
        return self.env.ref('account.account_invoices').report_action(self.invoice_id)


class SpaPaymentLine(models.TransientModel):
    _name = "spa.payment.line"
    _description = "Spa Payment Lines"

    payment_id = fields.Many2one('spa.payment', string="Payment")
    journal_id = fields.Many2one('account.journal', string="Journal")
    amount = fields.Monetary(string="Amount", default=0.0)
    currency_id = fields.Many2one(related="payment_id.currency_id")
    paid = fields.Boolean('Paid')
