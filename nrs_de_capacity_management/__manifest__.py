# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Capacity Management",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.1",
    "category": "",
    "depends": [
        'base', 
        'web',
        'mail',
        'product',
        'sale',
        'subscription_bill_run_tau',
    ],
    "data": [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'view/menu.xml',
        'view/ns_floor.xml',
        'view/ns_rooms.xml',
        'view/ns_pdu.xml',
        'view/ns_breaker.xml',
        'view/ns_space.xml',
        'view/ns_patchpanel.xml',
        'view/ns_ports.xml',
        'view/product.xml',
        'view/sale.xml'
    ],
    "qweb": [
    ],

    "license": 'LGPL-3',
    'installable': True
}
