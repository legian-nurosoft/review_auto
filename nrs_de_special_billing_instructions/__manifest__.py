# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Special Billing Instructions",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.2.0",
    "category": "",
    "depends": [
        'base',
        'web',
        'nrs_de_ramp_up_order',
        'sale',
        'sale_subscription',
        'nrs_de_origin_mrc',
        'web_studio'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/subscription_view.xml',
        'views/account_view.xml',
        'data/mail_template.xml',
        'data/style.xml'
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
