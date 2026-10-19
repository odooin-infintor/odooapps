# -*- coding: utf-8 -*-
{
    'name': "Multi-Level Approvals for Quotations, Vendor Bills & Vendor Payments",

    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    'summary': """
        Multi-Level Approvals for Quotations, Vendor Bills & Vendor Payments""",

    'description': """
       This module enhances Odoo's approval workflow by introducing multi-level approvals
       for Quotations to Purchase order,Vendor Bills and Vendor Payments.
    """,

    'author': "Infintor Solutions",
    'website': "https://www.infintor.com",
    'category': 'Accounting/Accounting',

    # any module necessary for this one to work correctly
    'depends': ['purchase'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.access.csv',
        'views/approver.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,

    # only loaded in demonstration mode
}