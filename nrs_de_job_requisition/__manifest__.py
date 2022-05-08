# -*- coding: utf-8 -*-

{
    "name": "Nurosoft Digital Edge Job Requisition",
    "author": "Nurosoft Consulting",
    "website": "www.nurosoft.id",
    "version": "1.0.0",
    "category": "",
    "depends": [
        "base",
        "hr",
        "hr_recruitment",
        "custom_mrc_nrc_jsi"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "data/job_requisition_stage_data.xml",
        "data/ir_sequence_data.xml",
        "view/hr_job.xml",
        "view/job_requisition_stage_views.xml",
        "view/job_requisition_views.xml",
        "view/qualification_tag_views.xml",
        "view/skill_tag_views.xml",
        "view/hr_applicant.xml",
        "view/hr_recruitment_stage.xml",
        "view/menu.xml",
        "view/hr_employee_view.xml",
        "view/res_users.xml"
    ],
    "qweb": [
    ],

    "license": "LGPL-3",
    "installable": True,
    "sequence": 9999
}
