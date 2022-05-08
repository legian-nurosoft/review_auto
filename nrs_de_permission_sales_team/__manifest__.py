# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Permission Sales Team",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.1",
    "category": "",
    "depends": [
        'base', 
        'web',
        'sale',
        'crm',
        'digital_edge_sale_approval',
        'subscription_bill_run_tau'
    ],
    "data": [
        'data/data.xml',
        'view/crm_team.xml',
        'view/sale.xml',
        'security/ir.model.access.csv',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
