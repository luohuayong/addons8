# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, SUPERUSER_ID
import logging, json, requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class ebiz_stock(models.Model):
    _inherit = 'ebiz.stock'

    def sync_stock_var(self, cr, uid, ids, context=None):
        """ 库存增量同步 """
        _logger.info('sync var')
        if not isinstance(ids,list):
            ids = [ids]
        sync_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        product_model = self.pool.get('product.product')
        partner_model = self.pool.get('res.partner')
        product_lines = []
        for ebiz_stock in self.read(cr, uid, ids, ['product_id','var_qty','sync_check']):
            if not ebiz_stock['sync_check']:continue
            guid_dict = product_model.read(cr, uid, ebiz_stock['product_id'][0], ['guid','seller_id'])
            guid = guid_dict and guid_dict['guid'] or ''
            seller_id = guid_dict['seller_id'] and guid_dict['seller_id'][0] or False
            seller = partner_model.browse(cr, uid, seller_id)
            # 准备字典
            product_lines.append({
                'sku_guid':guid,
                'sku_id':ebiz_stock['id'],
                'sync_qty':ebiz_stock['var_qty'],
                'storage_guid':seller.stock_warehouse_id.id and str(seller.stock_warehouse_id.id) or '',
                'storage_name':seller.stock_warehouse_id.name or '',
                'storage_alias':seller.stock_warehouse_id.x_delivery or '',
                })
        if product_lines:
            sync_dict = {'sync_date':sync_date,'product_lines':product_lines}
            res = self.pool['ebiz.shop'].remote_call(cr, uid, 'stock', 'increment_stocksync', **sync_dict)
            if res.get('result','failed') != 'success':
                if res.get('err_msg',''):
                    res_ids = res.get('err_msg')[:-1].split(';')
                    for res_id in res_ids:
                        if int(res_id) in ids:ids.remove(int(res_id))
        self.write(cr, uid, ids, {'sync_check':False})
        return True

    def sync_stock_qty(self, cr, uid, ids, context=None):
        """ 库存全量同步 """
        _logger.info('sync qty')
        if not isinstance(ids,list):
            ids = [ids]
        sync_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        product_model = self.pool.get('product.product')
        partner_model = self.pool.get('res.partner')
        product_lines = []
        for ebiz_stock in self.read(cr, uid, ids, ['product_id','stock_qty','sync_check']):
            if not ebiz_stock['sync_check']:continue
            guid_dict = product_model.read(cr, uid, ebiz_stock['product_id'][0], ['guid','seller_id'])
            guid = guid_dict and guid_dict['guid'] or ''
            seller_id = guid_dict['seller_id'] and guid_dict['seller_id'][0] or False
            seller = partner_model.browse(cr, uid, seller_id)
            # 准备字典
            product_lines.append({
                'sku_guid':guid,
                'sku_id':ebiz_stock['id'],
                'sync_qty':ebiz_stock['stock_qty'],
                'storage_guid':seller.stock_warehouse_id.id and str(seller.stock_warehouse_id.id) or '',
                'storage_name':seller.stock_warehouse_id.name or '',
                'storage_alias':seller.stock_warehouse_id.x_delivery or '',
                })
        if product_lines:
            sync_dict = {'sync_date':sync_date,'product_lines':product_lines}
            res = self.pool['ebiz.shop'].remote_call(cr, uid, 'stock', 'full_stocksync', **sync_dict)
            if res.get('result','failed') != 'success':
                if res.get('err_msg',''):
                    res_ids = res.get('err_msg')[:-1].split(';')
                    for res_id in res_ids:
                        if int(res_id) in ids:ids.remove(int(res_id))
        self.write(cr, uid, ids, {'sync_check':False})
        return True