# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Sale Approval",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.2.0",
    "category": "",
    "depends": [
        'base', 
        'web', 
        'digital_edge_sale_approval',
        'nrs_de_permission_sales_team',
        'sale_crm',
        'web_studio',
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/config.xml',
        'view/sale.xml',
        'data/data.xml',
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
