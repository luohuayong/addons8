# -*- coding:utf-8 -*-
from openerp import models, fields, api
from datetime import datetime


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    buhuo_qiyong = fields.Boolean(string=u"启用", default=False)
    buhuo_zhouqi = fields.Integer(string=u"补货周期")
    buhuo_riqi = fields.Date(string=u"最后一次补货时间")
    buhuo_jiange = fields.Integer(string=u"间隔天数", compute='_buhuo_jiange')
    buhuo_kucun = fields.Integer(string=u"当前库存",readonly=True)
    buhuo_shuliang = fields.Integer(string=u"补货总数量",readonly=True)
    buhuo_zhuangtai = fields.Selection([('0', u"-"), ('1', u"正常"), ('2', u"待补货"), ('3', u"紧急补货")],
                                       string="状态提醒", compute='_buhuo_zhuangtai')
    huojia_item_ids = fields.One2many('buhuo.huojia_item', 'warehouse_id', string=u"货架产品",readonly=True)

    @api.depends('buhuo_riqi')
    def _buhuo_jiange(self):
        for r in self:
            if not r.buhuo_riqi:
                r.buhuo_jiange = 999
            else:
                last_date = fields.Datetime.from_string(r.buhuo_riqi)
                r.buhuo_jiange = (datetime.now() - last_date).days

    @api.depends('buhuo_kucun', 'buhuo_shuliang')
    def _buhuo_zhuangtai(self):
        for r in self:
            if r.buhuo_kucun is None or r.buhuo_shuliang is None:
                r.buhuo_zhuangtai = '0'
            elif r.buhuo_kucun == 0:
                r.buhuo_zhuangtai = '3'
            elif r.buhuo_shuliang == 0:
                r.zhuangtai = '0'
            elif float(r.buhuo_kucun)/float(r.buhuo_shuliang) > 0.5:
                r.buhuo_zhuangtai = '1'
            elif float(r.buhuo_kucun)/float(r.buhuo_shuliang) > 0.3:
                r.buhuo_zhuangtai = '2'
            else:
                r.buhuo_zhuangtai = '3'
