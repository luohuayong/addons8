# -*- coding: utf-8 -*-
{
    'name': "电商订单开票及付款方式",

    'description': """
电商订单开票及付款方式"
====================================

模块功能
--------------------------------------------
    * 订单增加付款方式
    * 客户签收自动创建发票, 确认发票, 创建付款单
    * 计算优惠减款
""",

    'author': 'OSCG',
    'website': 'http://www.zhiyunerp.com',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'bysun_stock_product', 'account_voucher'],
    'data': [
        'security/ir.model.access.csv',
        'ebiz_account_data.xml',
        'wizard/replace_payment_wizard.xml',
        'views/sale.xml',
        'views/account.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

