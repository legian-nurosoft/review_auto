# -*- coding: utf-8 -*-

{
'name': 'subscription_bill_run_tau',
'version': '14.0.7.0',
'author': 'OdooHK-TAU',
'depends': ['sale_subscription','sale_project'],
'data': [
        'data/sale_order_cron.xml',
        "views/operating_country.xml",
        "views/operating_metros.xml",
        "views/operating_sites.xml",
        "views/account_move.xml",
        "views/menu.xml",
        'views/project_task_type_form_view.xml',
        'views/sale_order_form_view.xml',
        'views/sale_subscription_form_view.xml',
        'views/sale_subscription_wizard_form_view.xml',
        "views/product.xml",
        "views/project_task.xml",
        "security/ir.model.access.csv",
    ],
}
