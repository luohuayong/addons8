# -*- encoding: utf-8 -*-

{
    'name': '对账单据',
    'version': '1.0',
    "category" : "Account",
    'description': """银行对账功能\n
                     *显示银行对账明细行对应的源单据号\n""",
    'author': 'OSCG',
    'website': 'https://www.zhiyunerp.com/',
    'depends': ['account_accountant','hopin_project','bysun_account','account_bank_reconcile'],
    'init_xml': [ ],
    'data': [ 'views/account_bank_improve_view.xml',
              #'views/sale_quotation_sequence.xml',
            ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}