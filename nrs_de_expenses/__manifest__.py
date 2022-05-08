# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Expenses",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "15.0.1",
    "category": "",
    "depends": [
        'base',
        'web',
        'hr_expense',
        'nrs_de_account_assets',
    ],
    "data": [
        'views/hr_expenses.xml',
        'views/mail_template.xml',
        'security/ir.model.access.csv',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}