{
    "name": "Digital Edge Sale Approval",
    "summary": """
        Customized sale approval flow
        """,
    "category": "",
    "version": "14.0.1.0.0",
    "author": "Odoo PS",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    "depends": [
        'sale_crm',
        'product',
        'account',
        'sale_project',
        'sale_subscription',
        'subscription_bill_run_tau'
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_views.xml",
        "views/product.xml",
        "views/project.xml",
        "views/subscription.xml",
        "views/account_move.xml",
        "views/document.xml"
    ],
    "post_init_hook": '_sale_order_post_init',
    "task_id": [2560748],
}
