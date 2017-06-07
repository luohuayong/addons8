# -*- coding: utf-8 -*-
{
    'name': "存货收发存报表",

    'description': """
存货收发存报表
    """,

    'author': "xujl",

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views.xml',
        'wizard/report_stock.xml',
    ],
}