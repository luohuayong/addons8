# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-2015 OSCG (<http://www.zhiyunerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Stock Production',
    'version': '1.0',
    'category': 'Warehouse Management',
    'summary': '仓库加工管理',
    'sequence': 32,
    'description': """
仓库简单加工管理
====================================

仓库加工单形式
--------------------------------------------
    * 一对多加工：一个原料加工成多个成品，如三文鱼切割成鱼头、鱼身、鱼尾等不同成品。
    * 多对一加工：多个原料加工成一个成品，如多种水果包装成水果礼盒。
    
模块功能：
--------------------------------------------
    * 填写并审核仓库加工单，加工原料自动出库，加工成品自动入库
    * 加工单打印
    * 系统自动汇总加工单上的原料成本，按销售价格比例分摊到成品成本
    * 创建原料消耗、成品入库的会计凭证

""",
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': ['stock_account',],
    'data': [
        'stock_production_view.xml',
        'security/ir.model.access.csv',
        'stock_production_sequence.xml',
    ],
    'installable': True,
    'active': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
