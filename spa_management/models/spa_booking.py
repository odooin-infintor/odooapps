# -*- coding: utf-8 -*-
import math

import pytz
from datetime import datetime, timedelta
import logging
from odoo import api, fields, models,_
from odoo.exceptions import UserError,ValidationError


class SpaBooking(models.Model):
    _name = "spa.booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Spa Booking"
    _order = "name desc"

    name = fields.Char(string="Reference", default="New")
    partner_id = fields.Many2one('res.partner', string="Customer")
    partner_name = fields.Char("Customer Name")     # TODO: remove this
    partner_email = fields.Char("Email")   # TODO: change to related field
    partner_phone = fields.Char("Phone")   # TODO: change to related field
    branch_id = fields.Many2one('spa.branch', string="Branch")
    employee_id = fields.Many2one('hr.employee', string="Beautician")
    date = fields.Date(string="Booking Date", default=fields.Date.context_today)
    time_from = fields.Selection(selection="_selection_time_from", string="Time From")
    time_to = fields.Selection(selection="_selection_time_from", compute="_compute_time_to", string="Time To")
    state = fields.Selection([
        ('draft', 'Waiting'),
        ('check_in', 'Check In'),
        ('confirm', 'Check Out'),
        ('done', 'Done'),
        ('no_show', "No-Show"),
        ('cancel', 'Cancelled'),
        ], string="Status", default='draft',track_visibility='always')
    source = fields.Selection([
        ('direct', 'Direct'),
        ('phone', 'Telephone'),
        ('web', 'Website'),
        ], string="Booking via", default='direct')
    note = fields.Text(string="Note")
    order_id = fields.Many2one('sale.order', string="Order")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    payment_ids = fields.One2many('account.payment', 'booking_id', string="Payments")
    booking_line_ids = fields.One2many('spa.booking.line', 'booking_id', string="Services")
    check_in_time = fields.Datetime(string="Check In Time")
    check_out_time = fields.Datetime(string="Check Out Time")
    amount_total = fields.Monetary(compute="_compute_total_amount", string="Total")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    net_total = fields.Monetary(compute="_compute_total_amount", string="Net Total")
    # via_calendar = fields.Boolean(string='Via Calendar')
    overlap_timing = fields.Boolean(string='Overlap  Timings')

    @api.model
    def default_get(self, fields):
        res = super(SpaBooking, self).default_get(fields)
        if 'branch_id' not in res:
            res['branch_id'] = self.env.user.branch_id.id or self.env['spa.branch'].search([],limit=1).id or False
        return res

    @api.model
    def _selection_time_from(self):
        hr_start = 0
        hr_end = 24
        min_start = 0
        min_end = 60
        step = 5    # 5 Mins.
        vals = []
        while hr_start < hr_end:
            time_val = "%.0f:%.0f" % (hr_start, min_start)
            time_disp = "%02.0f:%02.0f" % (hr_start, min_start)
            vals.append((time_val, time_disp))
            min_start += step
            if min_start == min_end:
                min_start = 0
                hr_start += 1
        return vals

    @api.depends('booking_line_ids.product_id')
    def _compute_total_amount(self):
        for booking in self:
            booking.amount_total = sum(booking.booking_line_ids.mapped('unit_price'))
            booking.net_total = booking.invoice_id.amount_total

    @api.depends('time_from', 'booking_line_ids.product_id')
    def _compute_time_to(self):
        for rec in self:
            if rec.time_from:
                booking_lines = rec.booking_line_ids.filtered(lambda l: l.product_type == 'service')
                dur_hrs = sum(booking_lines.mapped('product_id.duration_hrs'))
                dur_mins = sum(booking_lines.mapped('product_id.duration_min'))
                if len((booking_lines)) > 0:
                    dur_hrs = sum(booking_lines[len(booking_lines) - 1].mapped('product_id.duration_hrs'))
                    dur_mins = sum(booking_lines[len(booking_lines) - 1].mapped('product_id.duration_min'))
                    new_start_time = booking_lines[len(booking_lines) - 1].from_time
                    start_time = new_start_time.split(':')
                else:
                    start_time = rec.time_from.split(':')
                # start_time = rec.time_from.split(':')
                total_mins = int(start_time[1]) + dur_mins
                total_hrs = int(start_time[0]) + dur_hrs
                hrs = total_hrs + (total_mins // 60)
                mins = total_mins % 60
                if hrs > 23:
                    raise UserError("Hours exceeds the limit")
                rec.time_to = "%.0f:%.0f" % (hrs, mins)
            else:
                rec.time_to = ''

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.update({'booking_line_ids': [(5,0,0)]})
        if self.partner_id:
            self.partner_phone = self.partner_id.phone or self.partner_id.mobile  or ''
            self.partner_email = self.partner_id.email or ''

            warnings = []
            for line in self.booking_line_ids:
                res = line._onchange_product_id() or {}
                msg = res.get('warning', {}).get('message', False)
                if msg:
                    warnings.append(msg)
            if warnings:
                return {'warning': {'title': 'Oops!', 'message': "\n".join(warnings)}}

    @api.model
    def get_calendar_data(self, branch, beautician, service):
        # if self.env.user.has_group('hr.group_hr_user') or self.env.user.has_group('hr.group_hr_manager'):
            Employee = self.env['hr.employee'].sudo()
            employee_domain = [('active', '=', True),('is_beautician', '=', True)]
            booking_domain = [
                ('booking_id.state', 'not in', ['cancel', 'no_show']),
                ('product_id.type', '=', 'service'),
            ]
            # block_booking_domain = [('active', '=', True)]
            leave_domain = [('state', '=', 'validate')]

            # Spa Branch
            branches = self.env['spa.branch'].search([])
            branch_data = [{'id': branch.id, 'name': branch.name} for branch in branches]

            # Beauticians
            if branch and branch != 'all':
                branch_id = int(branch)
                employee_domain.append(('branch_id', '=', branch_id))
                booking_domain.append(('booking_id.branch_id', '=', branch_id))
                # block_booking_domain.append(('branch_id', '=', branch_id))

            if service and service != '0':
                service_id = int(service)
                employee_domain.append(('product_ids.id', '=', service_id))

            employees = Employee.search(employee_domain)
            employees_data = [{'id': employee.id, 'title': employee.name} for employee in employees]

            if beautician and beautician != 'all':
                employee_id = int(beautician)
                employee_domain.append(('id', '=', employee_id))
                booking_domain.append(('employee_id', '=', employee_id))
                leave_domain.append(('employee_id', '=', employee_id))
                employees = Employee.search(employee_domain)

            # Resource
            resource_data = []
            for employee in employees:
                bus_hrs_list = []
                for shift in employee.work_shift_ids:
                        bus_hrs_list.append({
                        'dow': [int(shift.week_day)],
                        'start': '{0:02.0f}:{1:02.0f}'.format(*divmod(shift.shift_from * 60, 60)),
                        'end': '{0:02.0f}:{1:02.0f}'.format(*divmod(shift.shift_to * 60, 60)),
                        })
                resource_data.append({'id': employee.id, 'title': employee.name, 'businessHours': bus_hrs_list})

            # Bookings
            booking_data = []
            booking_lines = self.env['spa.booking.line'].search(booking_domain)
            for line in booking_lines:
                booking = line.booking_id

                color = {
                    'draft': '#f1c40f',
                    'check_in': '#2980b9',
                    'confirm': '#e74c3c',
                    'done': '#2ecc71',
                    'no_show': 'orange'
                }
                title =  "%s - %s - %s" % (
                    booking.partner_id.name or booking.partner_name or '',
                    booking.partner_phone or '',
                    line.product_id.name or '',
                )
                if booking.check_in_time:
                    title += " (%s)" % (booking.check_in_time + timedelta(hours=3)).strftime("%H:%M")

                if booking.source == 'web':
                    title += "\nVia-Website"

                booking_data.append({
                    'id': booking.id,
                    'resourceId': line.employee_id.id,
                    'title': title,
                    'resources': [line.employee_id.id],
                    'allDay': False,
                    'leave': False,
                    'backgroundColor': color[booking.state],
                    'start': line.from_date.strftime("%Y-%m-%d %H:%M"),
                    'end': line.to_date.strftime("%Y-%m-%d %H:%M"),
                })

            if self.env['ir.module.module'].sudo().search([('name', '=', 'hr_holidays'), ('state', '=', 'installed')]):
                leaves = self.env['hr.leave'].sudo().search(leave_domain)
                for leave in leaves:
                    leave_start = leave.request_date_from.strftime("%Y-%m-%d 00:00")
                    leave_end = leave.request_date_to.strftime("%Y-%m-%d 23:59")
                    if leave.request_unit_half:
                        if leave.request_date_from_period == 'am':
                            leave_start = leave.request_date_from.strftime("%Y-%m-%d 00:00")
                            leave_end = leave.request_date_from.strftime("%Y-%m-%d 13:00")
                        else:
                            leave_start = leave.request_date_from.strftime("%Y-%m-%d 13:00")
                            leave_end = leave.request_date_from.strftime("%Y-%m-%d 23:59")
                    elif leave.request_unit_hours:
                        leave_date = leave.request_date_from.strftime("%Y-%m-%d")
                        time_from = float(leave.request_hour_from)
                        time_to = float(leave.request_hour_to)
                        leave_start = "{0} {1:02.0f}:{2:02.0f}".format(leave_date, *divmod(time_from * 60, 60))
                        leave_end = "{0} {1:02.0f}:{2:02.0f}".format(leave_date, *divmod(time_to * 60, 60))

                    booking_data.append({
                        'id': leave.id,
                        'resourceId': leave.employee_id.id,
                        'start': leave_start,
                        'end': leave_end,
                        'rendering': 'background',
                        'backgroundColor': '#fb0c00',
                        'leave': True,
                        'allDay': False,
                    })

            services = self.env['product.product'].search([('sale_ok', '=', True), ('type', '=', 'service')])
            services_data = [{'id': service.id, 'name': service.display_name, 'template_id': service.product_tmpl_id.id} for service in services]

            res = {
                'date': fields.Date.context_today(self),
                'branches': branch_data,
                'employees': employees_data,
                'resources': resource_data,
                'bookings': booking_data,
                'services': services_data,
            }
            return res
        # else:
        #     raise UserError(
        #         _('Sorry! This User has no Access on Employees (Beauticians). Please contact Administrator to grant permission on Human Resources.')
        #         )

    def action_save(self):
        self.ensure_one()
        if self._context.get('calendar_booking', False):
            return {
                'type': 'ir.actions.client',
                'tag': 'calendar_booking',
            }
        return True

    def action_confirm(self):
        self.ensure_one()
        ctx = dict(self._context) or {}
        ctx.pop('default_date', None)
        if not self.partner_id:
            partner = self.env['res.partner'].with_context(ctx).create({
                'name': self.partner_name or '',
                'phone': self.partner_phone or '',
                'email': self.partner_email or '',
                'customer_rank': 1,
            })
            self.partner_id = partner.id

        

        order_lines = []
        for line in self.booking_line_ids:
            line_vals = {
                'product_id': line.product_id.id,
                'product_uom_qty': 1,
                'employee_id': line.employee_id.id,
            }
            order_lines.append((0, False, line_vals))
        if order_lines:
            order = self.env['sale.order'].with_context(ctx).create({
                'partner_id': self.partner_id.id,
                'branch_id': self.branch_id.id,
                'order_line': order_lines,
                'sale_type': 'booking',
            })
            order._onchange_branch_id()     # For updating Warehouse

            self.write({
                'order_id': order.id,
                'state': 'confirm',
                'check_out_time': datetime.now(),
            })

            return {
                'type': 'ir.actions.act_window',
                'views': [[False, 'form']],
                'name': 'Sale Order',
                'res_model': 'sale.order',
                'res_id': order.id,
                'context': {'calendar_booking': True, 'booking_id': self.id},
                'target': 'new',
            }
        else:
            self.state = 'done'
            return self.action_save()

    def action_pay(self):
        self.ensure_one()
        return self.order_id.action_confirm_booking()

    def action_draft(self):
        self.ensure_one()
        self.write({
            'state': 'draft',
            'order_id': False,
            'invoice_id': False,
        })
        return True

    def action_check_in(self):
        self.ensure_one()
        self.write({
            'state': 'check_in',
            'check_in_time': datetime.now(),
        })
        return self.action_save()

    def action_cancel(self):
        self.ensure_one()
        if self.order_id:
            self.order_id.action_cancel()
        if self.payment_ids:
            self.payment_ids.action_draft()
            self.payment_ids.cancel()
        if self.invoice_id:
            self.invoice_id.button_draft()
            self.invoice_id.button_cancel()
        self.state = 'cancel'

        return self.action_save()

    def action_no_show(self):
        self.ensure_one()
        self.state = 'no_show'
        return self.action_save()

    def action_spa_invoice_print(self):
        if self.invoice_id:
            # return self.env.ref('arabic_receipt.arabic_receipt_report_action').report_action(self.invoice_id)
            return self.env.ref('account.account_invoices').report_action(self.invoice_id)

        else:
            return False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('spa.booking') or 'New'
        res = super(SpaBooking, self).create(vals)
        return res


class SpaBookingLine(models.Model):
    _name = "spa.booking.line"
    _description = "Spa Booking Lines"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string="Item")
    description = fields.Text(string="Description")
    booking_id = fields.Many2one('spa.booking', string="Booking")
    user_id = fields.Many2one('res.users', string="Beautician")
    employee_id = fields.Many2one('hr.employee', string="Beautician")
    from_time = fields.Selection(selection="_selection_time_from", string="Time From")
    # time_from
    to_time = fields.Selection(selection="_selection_time_from", compute="_compute_to_time", string="Time To", store=True)
    unit_price = fields.Float(related="product_id.lst_price", string="Price")
    product_type = fields.Selection(related="product_id.type", store=False)
    currency_id = fields.Many2one(related="booking_id.currency_id")
    from_date = fields.Datetime(compute="_compute_block_period", string="From Date", store=True)
    to_date = fields.Datetime(compute="_compute_block_period", string="To Date", store=True)

    def name_get(self):
        res = super(SpaBookingLine, self).name_get()
        if self._context.get('show_beautician_name', False):
            res = []
            for line in self:
                name = "%s (%s)" % (line.employee_id.name, line.product_id.name)
                res.append((line.id, name))
        return res

    @api.model
    def _selection_time_from(self):
        hr_start = 0
        hr_end = 24
        min_start = 0
        min_end = 60
        step = 5    # 5 Mins.
        vals = []
        while hr_start < hr_end:
            time_val = "%.0f:%.0f" % (hr_start, min_start)
            time_disp = "%02.0f:%02.0f" % (hr_start, min_start)
            vals.append((time_val, time_disp))
            min_start += step
            if min_start == min_end:
                min_start = 0
                hr_start += 1
        return vals

    @api.depends('from_time', 'product_id')
    def _compute_to_time(self):
        for rec in self:
            if rec.product_type == 'service' and rec.from_time:
                dur_hrs = rec.product_id.duration_hrs or 0
                dur_mins = rec.product_id.duration_min or 0
                start_time = rec.from_time.split(':')
                total_mins = int(start_time[1]) + dur_mins
                total_hrs = int(start_time[0]) + dur_hrs
                hrs = total_hrs + (total_mins // 60)
                mins = total_mins % 60
                if hrs > 23:
                    raise UserError("Hours exceeds the limit")
                rec.to_time = "%.0f:%.0f" % (hrs, mins)
            else:
                rec.to_time = rec.from_time

    @api.depends('booking_id.date', 'from_time', 'to_time')
    def _compute_block_period(self):
        for line in self:
            booking_date_str = line.booking_id.date and line.booking_id.date.strftime("%Y-%m-%d") or False
            if booking_date_str and line.from_time:
                line.from_date = datetime.strptime("%s %s" % (booking_date_str, line.from_time), "%Y-%m-%d %H:%M")
            if booking_date_str and line.to_time:
                line.to_date = datetime.strptime("%s %s" % (booking_date_str, line.to_time), "%Y-%m-%d %H:%M")



    @api.onchange('product_id','from_time')
    def onchange_set_beautician_domain(self):
        domain = [
            ('is_beautician', '=', True),
            ('product_ids.id', '=?', self.product_id.product_tmpl_id.id),
            ('branch_id', '=', self.booking_id.branch_id.id),
        ]
        beauticians = self.env['hr.employee'].sudo().search(domain)
        avail_beauticians = beauticians.filtered(lambda r: r.check_availablity(self.from_date, self.to_date,self._origin.id,self.booking_id.name,self.booking_id.overlap_timing))
        if self.employee_id not in avail_beauticians:
            self.employee_id = False

        return {'domain': {'employee_id': [('id', 'in', avail_beauticians.ids)]}}


    @api.onchange('from_time', 'to_time')
    def _onchange_time(self):
        booking_date_str = self.booking_id.date and self.booking_id.date.strftime("%Y-%m-%d") or False
        line_objects = self.sudo().search([('employee_id','=',self.employee_id.id),('booking_id.date','=',self.booking_id.date),('booking_id.state', '!=','cancel')])

    @api.onchange('product_id', 'from_time')
    def _onchange_product_id(self):
        if self.product_id and self.product_id.resource_ids:
            branch_id = self.booking_id.branch_id.id
            res = self.product_id.check_resource_availablity(self.from_date, self.to_date, branch_id)
            if res:
                msg = "There is no available %s for %s" % (", ".join(res), self.product_id.name)
                self.product_id = False
                return {'warning': {'title': 'Oops!', 'message': msg}}


class MessageInherit(models.Model):

    _inherit = "mail.message"

    @api.model
    def default_get(self, fields):
        if self._context.get("calendar_booking", False):
            fields.remove("date")
        res = super(MessageInherit, self).default_get(fields)
        missing_author = 'author_id' in fields and 'author_id' not in res
        missing_email_from = 'email_from' in fields and 'email_from' not in res
        if missing_author or missing_email_from:
            author_id, email_from = self.env['mail.thread']._message_compute_author(res.get('author_id'),
                                                                                    res.get('email_from'),
                                                                                    raise_exception=False)
            if missing_email_from:
                res['email_from'] = email_from
            if missing_author:
                res['author_id'] = author_id
        return res