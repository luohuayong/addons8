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
    'depends': ['base', 'product','stock','sale','purchase','product_expiry','delivery'],
    'data': [
        'security/ir.model.access.csv',
        'ebiz_shop_view.xml',
        'sale_order_view.xml',
        'product_view.xml',
        'res_partner_view.xml',
        'ebiz_stock_data.xml',
        'stock_location_view.xml',
        'purchase_order_view.xml',
        'wizard/ebiz_product_sync_wizard.xml',
        'wizard/ebiz_stock_sync_wizard.xml',
        'wizard/ebiz_supplier_sync_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}