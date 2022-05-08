# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Invoice Statement",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.3",
    "category": "",
    "depends": [
        'base', 
        'web', 
        'account',
        'sale',
        'account_accountant',
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/report.xml',
        'view/invoice.xml',
        'view/payment_instruction.xml',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
