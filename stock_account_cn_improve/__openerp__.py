# -*- coding: utf-8 -*-
{
    'name': "存货核算升级",

    'description': """
        对存货核算模块的功能升级
    """,

    'author': 'OSCG Dev',
    'website': 'http://www.zhiyunerp.com',
    'category': 'Inventory',
    'version': '0.1',
    'depends': ['stock','bysun_picking','stock_account_cn'],
    'data': [
        'stock_account_cn_improve_view.xml',
        'stock_inventory_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

