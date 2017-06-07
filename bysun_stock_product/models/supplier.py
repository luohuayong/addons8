# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging
import uuid

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    guid = fields.Char(u'全球唯一识别码',copy=False)
    default_return_goods_address = fields.Char(u'默认退货地址')
    default_recipients = fields.Char(u'默认收件人')
    default_recipients_phone = fields.Char(u'默认收件人电话号码')
    supplier_mode = fields.Selection([('Direct_Procurement',u'直采'),
        ('Consign_stock_in',u'代售入仓'),
        ('Consign',u'代售不入仓'),
        ('Commission',u'佣金')],u'供应商类型')
    stock_warehouse_id = fields.Many2one('stock.warehouse', u'仓库')
    stock_location = fields.Many2one('stock.location',u'供应商库位')

    def sync_supplier(self, cr, uid, ids, context=None):
        _logger.info("syncing supplier")
        shop_obj = self.pool.get('ebiz.shop')
        result = {}
        for sup in self.browse(cr, uid, ids, context=context):
            if not sup.supplier:continue
            supplier = {
                'name': sup.name,
                'supplier':sup.guid,
                'default_return_goods_address':sup.default_return_goods_address,
                'default_recipients':sup.default_recipients,
                'default_tel':sup.mobile or sup.phone,
                'supplier_mode':sup.supplier_mode,
            }
            res = shop_obj.remote_call(cr, uid, 'supplier', 'suppliersync', **supplier)
            _logger.info(supplier)
            result.update({sup.id:res})
        return result

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not vals.get('guid',False):
            vals['guid'] = str(uuid.uuid1())
        return super(res_partner, self).create(cr, uid, vals, context=context)
