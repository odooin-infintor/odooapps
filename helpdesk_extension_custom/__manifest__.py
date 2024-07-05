# -*- coding: utf-8 -*-
{
    'name': "Helpdesk Extension",

    'summary': "Hold status for Helpdesk tickets with custom added reasons.",

    'description': """
        This module helps to mark the helpdesk tickets to hold state, with custom reasons.
    """,

    'author': "Infintor solutions",
    'website': "https://www.infintor.com",

    'category': 'Services/Helpdesk',
    'version': '17.0.1.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'helpdesk'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hold_reason.xml',
        'views/templates.xml',
        'views/views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
