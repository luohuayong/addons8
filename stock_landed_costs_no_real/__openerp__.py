# -*- encoding: utf-8 -*-

{
    'name': 'Landed Cost模块中去除real time valuation的限制',
    'version': '1.0',
    "category" : "Hidden",
    'description': """ 
    系统的落地成本分摊模块(Landed Cost)中，要求产品配置成“real time valuation”。此模块去除此限制，非real time valuation也允许分摊落地成本。
    1) 如果产品是real time valuation，则落地成本分摊同时，生成成本分摊的会计凭证；
    2) 如果产品不是real time valuation，则仅仅分摊成本到Quants，不生成会计凭证。
    """,
    'author': 'OSCG',
    'website': 'http://www.oscg.cn',
    'depends': ['stock_landed_costs'],
    'init_xml': [],
    'data': [ ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': True,
}