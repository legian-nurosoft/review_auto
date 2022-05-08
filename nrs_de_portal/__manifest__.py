# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Portal",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.1",
    "category": "",
    "depends": [
        "base",
        "web",
        "sale",
        "portal",
        "auth_totp",
        "subscription_bill_run_tau",
        "nrs_de_permission_sales_team",
        "helpdesk",
    ],
    "data": [
        "security/ir_config_parameter_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "view/portal.xml",
        "view/login.xml",
        "view/product.xml",
        "view/dashboard.xml",
        "view/sale.xml",
        "view/helpdesk_ticket.xml",
        "view/operating_country.xml",
        "view/operating_sites.xml",
        "data/mail_template.xml",
        "data/allowed_selection.xml",
        "view/res_config.xml",
        "view/res_partner.xml",
        "view/project.xml",
        'view/res_users_view.xml',
    ],
    "qweb": [
        "static/src/xml/*.xml"
    ],
    'external_dependencies': {
        'python': ['python-magic'],
    }, 
    "license": "LGPL-3",
    "installable": True
}
