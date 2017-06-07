# -*- encoding: utf-8 -*-

{
    'name': 'Exclude tax from cost for In price tax',
    'version': '1.0',
    "category" : "Purchase Management",
    'description': """ 
价内税Bug修正
====================================

含税价格情况下，订单总金额、税额、未税额的计算方法优化（尽量避免小数点误差的影响）
-------------------------------------------------------------------------------------------------------
    * 【Bug修正】含税价格采购的时候，采购入库价格（成本价格）中去除税额；
    * PO上，用总金额 减去 未税额 得到税额，而不是用 未税额 加 税额 得到总金额，后者的算法适合于价外税，前者的方法适合于价内税；
    * Invoice上，用总金额 减去 未税额 得到税额，而不是用 未税额 加 税额 得到总金额，后者的算法适合于价外税，前者的方法适合于价内税；
    * Invoice上，account.invoice.tax字段的税的计算方法修改成：修正所有税额之和，使其等于 ”总金额 减去 未税额“。
    * SO上，用总金额 减去 未税额 得到税额，而不是用 未税额 加 税额 得到总金额，后者的算法适合于价外税，前者的方法适合于价内税；
    
    """,
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': ['purchase', 'sale'],
    'init_xml': [],
    'data': [
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': False,
}