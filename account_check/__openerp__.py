# -*- coding: utf-8 -*-
{
    'name': "商品、供应商的会计设置检查",

    'description': """
1)自动设置商品的会计科目、税率，供应商的会计科目；
2)自动检查商品、供应商的会计科目、税率设置是否正确，列出不正确的商品、供应商条目。
""",

    'author': 'OSCG Dev',
    'website': 'http://www.zhiyunerp.com',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['product','purchase','account','hopin_project'],
    'data': [
        'wizard/account_check_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

