# -*- coding: utf-8 -*-

from openerp import models, fields, api
# 大仓分类
class bysunstock_category(models.Model):
    _name='bysunstock.category'
    _inherit = ['mail.thread']

    name=fields.Char(string=u'大仓分类名称')

