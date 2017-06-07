# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)
class product_template(models.Model):
    _inherit = 'product.template'

    validity=fields.Char(string=u'有效期')
    contraindication=fields.Char(string=u'食用禁忌')
    suggesteduse=fields.Char(string=u'食用方法')
    qualification=fields.Text(string=u'资质认证')

    packages_id=fields.Many2one('bysunpackages.category',u'包装种类名称')
    stock_id=fields.Many2one('bysunstock.category',u'大仓分类名称')

    delivery_range_id = fields.Many2many('res.country.state','res_province_product','id','delivery_range_id',u'配送范围')
    purchase_price = fields.Float(u'采购价')

    def _get_delivery_area(self, cr, uid, p, context=None):
        delivery_area=''
        for i in p.delivery_range_id:
            delivery_area+=i.name+','
        if delivery_area:
            delivery_area=delivery_area[0:-1]
        return delivery_area

    def _prepare_sync_vals(self, cr, uid, p, context=None):
        prod = super(product_template, self)._prepare_sync_vals(cr, uid, p, context=context)
        delivery_area=self._get_delivery_area(cr, uid, p, context=context)
        prod.update({'delivery_area': delivery_area or ''})
        prod.update({'packing_type': p.packages_id.name or ''})
        prod.update({'qualification': p.qualification or ''})
        prod.update({'edible_methods': p.suggesteduse or ''})
        prod.update({'validtime': p.validity or ''})
        prod.update({'edible_taboos': p.contraindication or ''})
        prod.update({'custom_warehouse': p.stock_id.name or ''})
        return prod

        # 同步商品增加组合商品验证
    def sync_product(self, cr, uid, ids, context=None):
        _logger.info("syncing product")
        shop_obj = self.pool.get('ebiz.shop')
        result = {}
        now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stockp_obj=self.pool.get('stock.production.line')
        stock_obj=self.pool.get('stock.production')
        productp_obj=self.pool.get('product.product')
        # _logger.info("111111111111111111111111111111111111111")
        for p in self.browse(cr, uid, ids, context=context):
            wnames=''
            if getattr(p, "is_combination"):
                # _logger.info("2222222222222222222222222222222222")
                _logger.info(p.id)
                product_id=productp_obj.search(cr, uid, [('product_tmpl_id', '=', p.id)], context=context)
                _logger.info(product_id)
                stock_id=stock_obj.search(cr, uid, [('product_id', 'in', product_id)], context=context)
                _logger.info(stock_id)
                pids = stockp_obj.search(cr, uid, [('product_order', 'in', stock_id)], context=context)
                _logger.info(pids)
                if not pids:
                    wnames += p.name + ','
            if wnames:
                raise exceptions.ValidationError(u'组合商品[%s]未组装,不可同步'%(wnames[0:len(wnames)-1]))

            vals = self._prepare_sync_vals(cr, uid, p, context=context)
            post_vals = {'product_info':vals}
            res = shop_obj.remote_call(cr, uid, 'product', 'productsync', **post_vals)
            if res.get('result','') == 'success':
                cr.execute("update product_template set sync_date = %s where id = %s",(now_date, p.id,))
            else:
                result.update({p:res.get('err_msg','')})
        if result:
            err_msg = ''
            for err in result:
                err_msg += '%s:%s\n'%(err.name_get()[0][1],result.get(err))
            raise exceptions.ValidationError(err_msg)
        return result

class product_brand(models.Model):
    _inherit = 'product.brand'
    # 删除品牌时校验该品牌是否有商品
    def unlink(self, cr, uid, ids, context=None):
        # logging.info("1111111111")
        # product_model = self.pool['product.template']
        product_obj=self.pool.get('product.template')
        brand_obj=self.pool.get('product.brand')
        # logging.info(ids)

        wnames=''
        for brand in brand_obj.browse(cr, uid, ids , context=context):
            # logging.info(id)
            pids = product_obj.search(cr, uid, [('brand_id', '=', brand.id)], context=context)
            logging.info(brand.name)
            # logging.info(brand.name.encode("utf-8"))
            if pids:
                wnames += brand.name + ','
                # wnames.append(brand.name)
        logging.info(wnames)
        if wnames:
            # logging.info('11111')
            raise exceptions.ValidationError(u'品牌%s内有商品,不可删除'%(wnames))
        # logging.info(wids)
        # return False
        return super(product_brand, self).unlink(cr, uid, ids, context=context)
