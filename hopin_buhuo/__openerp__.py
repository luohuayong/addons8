# -*- coding: utf-8 -*-
{
    'name': "能量加油站-自动补货",
    'summary': "补货预警, 货架销售, 补货参数配置",
    'description': """
    
补货周期查询
---------------------------------------------------------
* ‘最后一次补货时间’是指司机从仓库将货拖走的日期
* ‘补货周期’是指渠道部给货架指定的标准补货间隔天数

货架库存预警
---------------------------------------------------------
* 货架当前剩余库存的总数量（A）
* 最后一次补货的商品总数量（B）
* 当A/B>50%的时候，提示‘正常’
* 当A/B<=50%的时候，提示‘待补货’
* 当A/B<=30%的时候，提示‘紧急补货’
* 货架在售的单个商品的剩余数量（a）
* 最后一次补货的该商品的补货数量（b）
* 当a/b>50%的时候，提示‘正常’
* 当a/b<=50%的时候，提示‘待补货’
* 当a/b<=30%的时候，提示‘紧急补货’

货架销售查询
----------------------------------------------------------
* 查询特定时间段内，某货架的总销量、总销额，并将销额最好的货架显示在最上面
* 查询特定时间段内，某货架所销售商品的数量、金额，并将销量最好的商品显示在最上面

    """,

    'author': "佰昌网络科技",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'product', 'bysun_stock_product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/canshu.xml',
        'views/zhouqi.xml',
        'views/huojia.xml',
        'views/xiaoshou_item.xml',
        'views/wizard.xml',
        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'application': True,
}
