# -*- coding: utf-8 -*-
{
    'name': "hopin_excel",

    'summary': """
        自己开发的报表模块""",

    'description': """
        自己开发的报表模块
    """,

    'author': "hopin",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'sale_income_total.xml',
        'stock_total.xml',
        'import_excel.xml',
        'ebiz_supplier_account_line_excel.xml',
        'borrow_goods.xml',
        'hopinsale_detail.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}