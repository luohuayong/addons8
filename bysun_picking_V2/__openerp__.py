# -*- encoding: utf-8 -*-

{
    'name': '仓库打单、拣货、验货、打包、出库处理',
    'version': '2.0',
    "category" : "Warehouse Management",
    'description': """
    * 拣货波次划分，配送路线/快递分配
    * 拣货打单：汇总拣货单、客户发货单、摘果投篮一次拣货单
    * 多仓库拣货时候，分库区打拣货单
    * 包裹标签打印
    * 条码验货、打包、出库
    """,
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': ['bysun_picking'],
    'init_xml': [],
    'data': [
        'picking_view.xml', 
        'sale_view.xml',
        'wizard/picking_to_wave_view.xml'
     ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': False,
    'qweb': [],
}