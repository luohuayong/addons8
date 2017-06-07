# -*- coding: utf-8 -*-
{
    'name': "产品同步，库存同步",
    'description': """
====================================

模块功能
--------------------------------------------
    """,

    'author': "OSCG",
    'website': "http://www.zhiyunerp.com",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['stock', 'bysun_stock_product'],
    'data': [
        'sale_order_view.xml',
        'res_partner_view.xml',
        'stock_location_view.xml',
        'product_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}