# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Subscription",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.0",
    "category": "",
    "depends": [
        "base",
        "product", 
        "sale",
        "sale_subscription",
        "sale_project",
        "web_studio",
    ],
    "data": [
        "security/ir.model.access.csv",
        "view/sales.xml",
        "view/subscription.xml",
        "view/change_subscription_wizard.xml",
        "view/adjust_billing_wizard.xml",
        "view/project_task_view.xml",
    ],
    "qweb": [
    ],

    "license": "LGPL-3",
    "installable": True,
    "sequence": 9999
}
