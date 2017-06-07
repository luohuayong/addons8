# -*- coding: utf-8 -*-
{
    'name': "能量加油站-自动补货",

    'description': """
        #### v0.1
        - abc
        - abc
    """,

    'author': "佰昌网络科技",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'product','bysun_stock_product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/canshu.xml',
        'views/zhouqi.xml',
        'views/huojia.xml',
        'views/xiaoshou_item.xml',
        'views/wizard.xml',
        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'application': True,
}
