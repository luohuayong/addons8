# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': '批次号上增加生产日期',
    'version': '1.0',
    "category" : "Warehouse Management",
    'description': """
批次号上增加生产日期
====================================

模块功能
--------------------------------------------
    * 批次上增加生产日期字段
    * 批次有效日期等基于生产日期计算，而不是当天日期计算
    * 批次码默认生成规则修改为 生产日期+序列号
    """,
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com',
    'depends': ['stock','product_expiry'],
    'data': [
        'lots_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: