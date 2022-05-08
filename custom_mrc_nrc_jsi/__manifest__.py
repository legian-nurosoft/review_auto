# -*- coding: utf-8 -*-

{
    'name': "Digital Edge Custom-jsi",
    'version': '14.0.1',
    'author': 'OdooHK - jsi',
    'depends': ['sale', 'crm', 'sale_subscription', 'web_studio', 'hr', 'project'],
    'data': [
        'views/assets.xml',
        'views/crm_fx_views.xml',
        'views/crm_views.xml',
        'views/sale_views.xml',
        'views/sale_report_template.xml',
        'views/partner.xml',
        'views/account.xml',
        'views/hr.xml',
        'views/project.xml',
        'views/subscription.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision.xml'
    ],
    'qweb': [
        'static/src/xml/fields.xml'
    ]
}
