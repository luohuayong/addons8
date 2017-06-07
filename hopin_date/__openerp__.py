# -*- coding: utf-8 -*-
{
    'name': "hopin_date",

    'summary': """
         临时功能 审核取消订单""",

    'description': """
        临时功能 审核取消订单
    """,

    'author': "ljun",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hopin_project'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'check_xml.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}