# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Ramp-Up Order",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.2.0",
    "category": "",
    "depends": [
        'base', 
        'web', 
        'sale_subscription',
        'subscription_bill_run_tau',
        'web_studio',
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/assets.xml',
        'view/sale.xml',
        'view/project.xml',
        'wizard/sale_ramp_ups.xml',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
