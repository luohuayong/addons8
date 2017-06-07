# -*- coding: utf-8 -*-
{
    'name': "ems面单接口与格式",

    'description': """
        1)EMS面单接口
        2)EMS面单打印格式
    """,

    'author': 'OSCG Dev',
    'website': 'http://www.zhiyunerp.com',
    'category': 'EMS Delivery',
    'version': '0.1',
    'depends': ['stock','bysun_stock_product','bysun_delivery'],
    'data': [
        'wizard/logistics_print.xml',
        'report/ems_delivery_report_template.xml',
        'ems_report.xml',
        'ems_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

