# -*- coding: utf-8 -*-
{
    'name': "界面配置",

    'description': """
界面配置"
====================================

模块功能
--------------------------------------------
    * 用代码实现界面配置的功能
""",

    'author': 'OSCG',
    'website': 'http://www.zhiyunerp.com',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'bysun_stock_product'],
    'data': [
        #'security/ir.model.access.csv',
        #'views/sale_view.xml',
        #'views/account_view.xml',
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

