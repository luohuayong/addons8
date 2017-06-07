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
    * SO、出库单上增加配送时段字段
    * 物流签收单打印
    * 包裹号批量扫描，包裹批量配送出库
    * 配送路线、配送车辆、配送司机、配送排班管理
    """,
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': [ 'bysun_picking'],
    'init_xml': [],
    'data': [
        'views/templates.xml',
        'wizard/delivery_wave_view.xml',
        'wizard/logistics_print.xml',
        'report/delivery_report_template.xml',
        'delivery_report.xml',
        'delivery_view.xml',
     ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': False,
}