# -*- coding: utf-8 -*-

from datetime import date

from odoo import api, fields, models


class SpaSummaryReport(models.TransientModel):
    _name = "spa.summary.report"
    _description = "Summary Report"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    branch_id = fields.Many2one('spa.branch', string="Branch")

    def prepare_report_data(self):
        # SUMMARY
        sales_summary_list = []
        sales_summary_total = 0
        summary_list = []
        summary_total = 0

        domain = [('state', 'in', ['sale', 'done']), ('branch_id', '=', self.branch_id.id)]
        if self.from_date:
            domain += [('date_order', '>=', self.from_date.strftime('%Y-%m-%d'))]
        if self.to_date:
            domain += [('date_order', '<=', self.to_date.strftime('%Y-%m-%d'))]

        orders = self.env['sale.order'].search(domain)

        order_lines = orders.filtered(lambda r: r.sale_type in ['normal', 'booking']).mapped('order_line')

        # Products
        product_lines = order_lines.filtered(lambda r: r.product_id.type != 'service')
        product_sale_total = sum(product_lines.mapped('price_subtotal'))
        sales_summary_list += [{'item': 'Products:', 'total': '%.2f' % product_sale_total}]
        sales_summary_total += product_sale_total

        # Services
        service_lines = order_lines.filtered(lambda r: r.product_id.type == 'service')
        service_sale_total = sum(service_lines.mapped('price_subtotal'))
        sales_summary_list += [{'item': '+ Services:', 'total': '%.2f' % service_sale_total}]
        sales_summary_total += service_sale_total

        domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.branch_id', '=', self.branch_id.id),
        ]
        if self.from_date:
            domain += [('move_id.invoice_date', '>=', self.from_date.strftime('%Y-%m-%d'))]
        if self.to_date:
            domain += [('move_id.invoice_date', '<=', self.to_date.strftime('%Y-%m-%d'))]

        # Tax
        summary_list += [{'item': '+ Total Tax:', 'total': '0.00'}]

        # Return
        summary_list += [
            {'item': '- Product Returns:', 'total': '0.00'},
            {'item': '- Service Returns:', 'total': '0.00'}]

        domain = [('type', '=', 'withheld'), ('employee_id.branch_id', '=', self.branch_id.id)]
        if self.from_date:
            domain += [('date', '>=', self.from_date.strftime('%Y-%m-%d'))]
        if self.to_date:
            domain += [('date', '<=', self.to_date.strftime('%Y-%m-%d'))]

        # PAYMENTS
        payment_list = []
        payment_total = {
            'total_in': 0,
            'total_out': 0,
            'total_net': 0,
        }
        journals = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])])
        domain = [('state', 'not in', ['draft', 'cancel']), ('branch_id', '=', self.branch_id.id)]
        if self.from_date:
            domain += [('date', '>=', self.from_date.strftime('%Y-%m-%d'))]
        if self.to_date:
            domain += [('date', '<=', self.to_date.strftime('%Y-%m-%d'))]
        payments = self.env['account.payment'].search(domain)
        for journal in journals:
            in_payments = payments.filtered(lambda r: r.journal_id.id == journal.id and r.payment_type == 'inbound')
            out_payments = payments.filtered(lambda r: r.journal_id.id == journal.id and r.payment_type == 'outbound')
            in_total = sum(in_payments.mapped('amount'))
            out_total = sum(out_payments.mapped('amount'))
            net_total = in_total - out_total
            payment_list.append({
                'name': journal.name,
                'in': '%.2f' % in_total,
                'out': '%.2f' % out_total,
                'net': '%.2f' % net_total,
            })
            payment_total['total_in'] += in_total
            payment_total['total_out'] += out_total
            payment_total['total_net'] += net_total

        # EMPLOYEE DETAILS
        employee_list = []
        employee_total = {
            'products': 0,
            'services': 0,
            'total': 0,
        }
        employees = self.env['hr.employee'].search([('is_beautician', '=', True), ('branch_id', '=', self.branch_id.id)])
        for employee in employees:
            product_sale = product_lines.filtered(lambda r: r.employee_id.id == employee.id)
            product_sale_total = sum(product_sale.mapped('price_subtotal'))
            service_sale = service_lines.filtered(lambda r: r.employee_id.id == employee.id)
            service_sale_total = sum(service_sale.mapped('price_subtotal'))
            product_service_total = product_sale_total + service_sale_total
            employee_list.append({
                'id': employee.id,
                'name': employee.name,
                'products': '%.2f' % product_sale_total,
                'services': '%.2f' % service_sale_total,
                'total': '%.2f' % product_service_total,
            })
            employee_total['products'] += product_sale_total
            employee_total['services'] += service_sale_total
            employee_total['total'] += product_service_total

        date_range = "(%s - %s)" % (
            self.from_date and self.from_date.strftime('%d-%m-%Y') or 'Beginning',
            self.to_date and self.to_date.strftime('%d-%m-%Y') or date.today().strftime('%d-%m-%Y'),
        )

        # REPORT DATA
        data = {
            'branch': self.branch_id.name,
            'date_range': date_range,
            'sales_summary': sales_summary_list,
            'sales_summary_total': '%.2f' % sales_summary_total,
            'summary': summary_list,
            'summary_total': '%.2f' % (summary_total + sales_summary_total),
            'payments': payment_list,
            'payment_total': payment_total,
            'employees': employee_list,
            'employee_total': employee_total,
        }
        return data

    def action_print(self):
        self.ensure_one()
        data = self.prepare_report_data()
        return self.env.ref('spa_management.spa_summary_report_action').report_action(self, data=data)
