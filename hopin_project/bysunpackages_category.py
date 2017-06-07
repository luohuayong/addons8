# -*- coding: utf-8 -*-
from openerp import models, fields, api
# 包装种类
class bysunpackages_category(models.Model):
    _name='bysunpackages.category'
    _inherit = ['mail.thread']

    name=fields.Char(string=u'包装种类名称')