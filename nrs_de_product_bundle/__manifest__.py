# -*- coding: utf-8 -*-
{
    'name': "Nurosoft DE Product Bundle",
    'summary': """This module is for create project bundle""",
    'description': """
        Write the module description here
    """,
    'author': "i am a developer",
    'website': "http://www.nurosoft.id",
    'category': 'sales',
    'version': '2',
    'depends': ['base', 'sale_management', 'product', 'subscription_bill_run_tau', 'account'],
    'data' :[
        'security/ir.model.access.csv',
        'views/product_bundle_views.xml',
        'views/product_bundle_menus.xml',
        'views/product_bundle_line_views.xml',
        'views/product_bundle_so_views.xml',
        ],
}