# -*- coding: utf-8 -*-
{
    'name': "网络公司",

    'summary': """
       版本迭代
        """,

    'description': """
        商品新加字段并同步至商城，订单列表添加支付方式,自动审单功能 2016/4/21----
        份tree中添加保质期和剩余保质期 自动审单功能添加库存判断2016/5/9

        -----V1.0.2更新内容 2016-06-20 到 2016-06-25----
        1.采购订单审核
        2.供应商邮费设置并自动生成邮费补贴
        3.供应商和产品要匹配到采销员和采销经理
        4.导出订单信息交货地址现实顺序
        5.订单信息显示正确的收货人电话
        ---------------

    """,

    'author': "ljun",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['product_expiry','bysun_sale','bysun_account', 'bysun_picking','bysun_stock_product', 'account_voucher','stock','bysun_customer_complain'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'product_view.xml',
        'order_view.xml',
        'packages_category_view.xml',
        'stock_category_view.xml',
        'sale_order.xml',
        'stock_quant.xml',
        'stock.xml',
        'supplier_view.xml',
        'account_invoice.xml',
        'stock_picking.xml',
        'ebiz_customer_complain_view.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo.xml',
    # ],
}