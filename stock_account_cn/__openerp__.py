# -*- encoding: utf-8 -*-

{
    'name': '适合中国财务要求的存货核算',
    'version': '1.0',
    "category" : "Hidden",
    'description': """
存货核算功能改善
====================================

存货核算中，系统存在的问题
--------------------------------------------
    * 系统存货核算的实现方法是入库、出库时候自动生成会计凭证。实践中，这个方法的问题是，每一条Stock Move生成一个凭证，自动生成的会计凭证太多，不适合会计人员进一步处理，同时也影响性能。
    * 销售出库、生产领料出库、盘亏出库等不同入出库原因，会计凭证科目不同，系统中无法为不同出入库原因设置不同会计科目。
    * 缺乏成本价格调整功能：系统采购入库的Stock Move， Stock Quants上的成本价格取值PO价格，如果PO价格错了，或发票价格和PO价格，系统缺乏Stock Move和Stock Quants的成本价格调整功能。

功能改善
--------------------------------------------
    * 在入库单、出库单、盘点单上增加Wizard，由会计人员点击Wizard生成相应会计凭证。
    * 系统的库存价值分析（Current Inventory Valuation）功能中，为了区分采购入库、暂估入库、采购退货、销售退货等不同的存货变动情况，增加Picking Type 和Invoice State两个字段用于存货价值分析。
    * 增加成本价格调整单（stock.cost.adjust）：选定商品及入库的Stock Move，输入调整价格，系统自动更新该Stock Move的价格，以及Stock Quants的价格，以及从该Stock Quants出库的所有Stock Move及Stock Quants的成本价格。
    
    """,
    'author': 'OSCG',
    'website': 'http://www.zhiyunerp.com',
    'depends': ['stock_account','bysun_supplier_account','bysun_customer_complain'],
    'init_xml': [],
    'data': [  'wizard/stock_picking_entry_view.xml', 
               'wizard/stock_inventory_entry_view.xml', 
               'stock_valuation_history_view.xml',
               'stock_cost_adjust_view.xml',
               'stock_cost_adjust_sequence.xml',
               'security/ir.model.access.csv',
               
                
     ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': False,
}