# -*- encoding: utf-8 -*-

{
    'name': '订单物流配送',
    'version': '1.0',
    "category" : "Warehouse Management",
    'description': """ 
电商订单物流配送
====================================

模块功能
--------------------------------------------
    * 订单物流配送第二次发布
    """,
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': [ 'bysun_delivery','bysun_picking_V2'],
    'init_xml': [],
    'data': [
        'delivery_view.xml',
        'delivery_data.xml',
     ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': False,
}