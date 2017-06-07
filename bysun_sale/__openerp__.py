# -*- coding: utf-8 -*-
{
    'name': "电商订单同步到ERP的SO",
    'description': """
电商订单同步到ERP的SO"
====================================

模块功能
--------------------------------------------
    * Sale Order上增加接口create_order，电商网站订单审核时候，调用该接口将订单推送到ERP。
    """,

    'author': "OSCG",
    'website': "http://www.zhiyunerp.com",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'sale', 'bysun_account', 'bysun_picking','bysun_stock_product'],
    'data': [
        'security/ir.model.access.csv',
        'res_partner_view.xml',
        'ebiz_sale_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}