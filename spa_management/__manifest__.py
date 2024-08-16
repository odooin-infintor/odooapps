# -*- coding: utf-8 -*-

{
    'name': 'SPA / SALON Management Core',
    'summary': "Infintor Spa Managemnet Solution",
    'sequence': 10,
    'version': '16.0.1.0',
    'license': 'OPL-1',
    'author': "Infintor Solutions",
    "price": 599,
    "currency": 'USD',
    'website': "https://www.infintor.com",
    'category': 'Sales',
    'description': """
        This module helps to manage customers, bookings and services provided by a SPA or Saloon.
    """,
    'depends': [
        'account',
        'purchase',
        'sale_stock',
        'hr',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rule.xml',

        'data/in_spa_data.xml',
        'views/in_spa.xml',


        'report/spa_summary_report_template.xml',
        'report/spa_summary_report.xml',
        'report/sale_report_views.xml',
        'report/booking_report_views.xml',

        'wizard/register_payment_view.xml',
        'wizard/summary_report_view.xml',

        'views/res_users_views.xml',
        'views/employee_views.xml',
        'views/product_views.xml',
        'views/spa_branch_views.xml',
        'views/spa_booking_views.xml',
        'views/sale_order_views.xml',
        'views/invoice_views.xml',
        'views/payment_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/resource_views.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
                'web.assets_backend': [
                    'spa_management/static/lib/css/fullcalendar.min.css',
                    'spa_management/static/lib/css/scheduler.min.css',
                    'spa_management/static/src/css/calendar_booking.css',
                    'spa_management/static/lib/js/moment.min.js',
                    'spa_management/static/lib/js/fullcalendar.min.js',
                    'spa_management/static/lib/js/scheduler.min.js',
                    'spa_management/static/src/js/calendar_booking.js',
                    'spa_management/static/src/xml/calendar.xml'
                ],
                },
}
