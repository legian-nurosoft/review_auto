# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Origin MRC",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.0",
    "category": "",
    "depends": [
        'base', 
        'sale_subscription',
        'account',
        'subscription_bill_run_tau', # Need depend to this module, because origin invoice deleted on this module. 
    ],
    "data": [
        'view/invoice.xml',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
