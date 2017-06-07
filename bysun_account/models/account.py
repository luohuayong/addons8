# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    fapiao = fields.Boolean(string=u"要发票", copy=False, readonly=True, )
    fp_text = fields.Char(u'开票内容', copy=False, readonly=True, )


class account_journal(models.Model):
    _inherit = 'account.journal'

    website_code = fields.Char(u'网站付款方式编码', required=True)

    _sql_constraints = [
        ('default_website_code_uniq', 'unique (website_code)', u'网站付款方式编码(website_code)必须唯一 !')
    ]

