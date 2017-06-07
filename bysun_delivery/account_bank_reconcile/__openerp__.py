# -*- coding: utf-8 -*-
{
    'name': "电商订单对账",

    'description': """
        电商订单对账
    """,

    'author': 'OSCG Dev',
    'website': 'http://www.zhiyunerp.com',
    'category': 'Bank',
    'version': '0.1',
    'depends': ['account_accountant','hopin_project'],
    'data': [
        'wizard/account_bank_statement_wizard_view.xml',
        'account_bank_statement.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

