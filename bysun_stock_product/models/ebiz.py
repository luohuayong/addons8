# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, SUPERUSER_ID
import logging, json, requests
from datetime import datetime

_logger = logging.getLogger(__name__)


class ebiz_shop(models.Model):
    _name = 'ebiz.shop'
    _description = '电商店铺'

    name = fields.Char(u'店铺名称', size=16, required=True)
    code = fields.Char(u'店铺前缀', size=8, required=True, help=u"系统会自动给该店铺的订单编号、客户昵称加上此前缀。通常同一个平台的店铺，前缀设置成一样")
    categ_id = fields.Many2one('product.category', string=u"默认商品分类", required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u"店铺仓", required=True)
    stock_date = fields.Datetime(u'最近库存同步时间', readony=True)
    # picking_type_id = fields.Many2one('stock.picking.type', u'不同步库存的操作类型')
    picking_type_ids = fields.Many2many('stock.picking.type', 'ebiz_shop_picking_type', 'shop_id', 'picking_type_id', u'不同步库存的操作类型', )

    host = fields.Char(u'地址(域名,IP)')
    user = fields.Char(u'用户名')
    pwd = fields.Char(u'密码')

    @api.model
    def remote_call(self, method_type, method_name, **kwargs):
        shops = self
        if not len(shops):
            shops = self.search([])

        if not shops:
            raise exceptions.MissingError(u'没有定义电商店铺')

        shop = shops[0]
        base_url = shop.host if shop.host.startswith('http') else 'http://' + shop.host
        base_url = base_url[0:-1] if base_url.endswith('/') else base_url
        service_uri = "%s/erp/%s/%s" % (base_url, method_type, method_name)

        headers = {}
        headers['Auth_Account'] = shop.user
        headers['Auth_Token'] = shop.pwd
        headers['Content-Type'] = "application/json; charset=utf-8"
        data = json.dumps(kwargs)
        _logger.info(data)
        resp = requests.post(service_uri, data, headers=headers)
        _logger.info(resp)

        res = {}
        if requests.codes.ok == resp.status_code:
            res = json.loads(resp.content)
            _logger.info(res)
            if 'success' == res.get('result'):
                _logger.info(u'%s调用成功' % method_name)
            else:
                _logger.error(u'%s调用失败, 原因:%s' % (method_name, res.get('err_msg')))
        else:
            _logger.error(u'http调用失败, 返回码: %s' % resp.status_code)
            res.update({'result':'failed','err_msg':''})

        return res



class ebiz_stock(models.Model):
    _name = 'ebiz.stock'
    _description = u"电商店铺库存同步"
    _rec_name = 'product_id'

    shop_id = fields.Many2one('ebiz.shop', string=u"店铺", required=True)
    location_id = fields.Many2one('stock.location', string=u"店铺库位", required=True)
    product_id = fields.Many2one('product.product', string=u"产品", required=True)
    sync_date = fields.Datetime(string=u"最近同步时间", readonly=True)
    var_qty = fields.Integer(string=u"增量同步数量", readonly=True)
    stock_qty = fields.Integer(string=u"全量同步数量", readonly=True)
    sync_check = fields.Boolean(string=u"要否同步", )

    _location_shop = {}

    def stock_reserve_changed(self, cr, uid, reserve, adjust_qty, context=None):
        """
        锁货引起的库存调整
        """
        shop_obj = self.pool.get('ebiz.shop')
        dataobj = self.pool.get('ir.model.data')

        location_src_id = reserve.location_id.id
        location_dest_id = dataobj.xmlid_to_res_id(cr, uid, 'ebiz_stock.stock_location_reserve')
        if adjust_qty < 0:
            location_src_id = location_src_id
            location_dest_id = reserve.location_id.id
            # adjust_qty = -adjust_qty

        shop_ids = shop_obj.search(cr, uid, [('warehouse_id.lot_stock_id', 'in', [location_src_id, location_dest_id])], context=context)
        if not shop_ids:
            _logger.info(u'非库存库位的移动或者不需要同步库存的操作类型, 不做库存增量计算.')
            return False

        shop_id = shop_ids[0]
        # 锁货单需要使用源库位来计算库存增(减)量
        return self._stock_changed(cr, uid, reserve.product_id.id, adjust_qty, location_src_id, shop_id, context=context)

    def stock_move_changed(self, cr, uid, move, qty, context=None):
        """"
        库存移动引起的库存调整
        """
        shop_obj = self.pool.get('ebiz.shop')

        # location_src_id = move.location_id.id
        # location_dest_id = move.location_dest_id.id
        domain = []
        # domain = [('warehouse_id.lot_stock_id', 'in', [location_src_id, location_dest_id])]
        if move.picking_id and move.picking_id.picking_type_id:
            domain += [('picking_type_ids', 'not in', [move.picking_id.picking_type_id.id])]

        shop_ids = shop_obj.search(cr, uid, domain, context=context)
        if not shop_ids:
            _logger.info(u'非库存库位的移动或者不需要同步库存的操作类型, 不做库存增量计算.')
            return False

        shop_id = shop_ids[0]
        return self._stock_changed_qty(cr, uid, move, shop_id, context=context)

    def _stock_changed_qty(self, cr, uid, move, shop_id, context=None):
        shop_obj = self.pool.get('ebiz.shop')
        shop = shop_obj.browse(cr, uid, shop_id, context=context)
        location_id = shop.warehouse_id.lot_stock_id.id
        if move.location_id.is_sync and move.location_dest_id.is_sync:
            _logger.info(u'源库位目的库位均为需要同步的库位, 不做库存增量计算.')
            return True
        elif not move.location_id.is_sync and not move.location_dest_id.is_sync:
            _logger.info(u'源库位目的库位均为不需要同步的库位, 不做库存增量计算.')
            return True
        product_qty = 0
        if move.location_id.is_sync:
            product_qty = - move.product_uom_qty
        if move.location_dest_id.is_sync:
            product_qty = move.product_uom_qty
        vals = {
            'shop_id':shop_id,
            'location_id':location_id,
            'product_id':move.product_id.id,
            'sync_check':True,
        }
        ids = self.search(cr, uid, [('shop_id', '=', shop_id), ('location_id', '=', location_id),
                                    ('product_id', '=', move.product_id.id), ('sync_check', '=', True)], context=context)
        if ids:
            self.write(cr, uid, ids, vals, context=context)
            for s in self.read(cr, uid, ids, ['var_qty'], context=context):
                self.write(cr, uid, [s['id']], {'var_qty': s['var_qty'] + product_qty}, context=context)
        else:
            vals.update({'var_qty': product_qty})
            self.create(cr, uid, vals, context=context)
        _logger.info(vals)

        return True


    def _stock_changed(self, cr, uid, product_id, product_qty, dest_location_id, shop_id, context=None):
        """
        库存发生变化时候，调用此方法更新 店铺库存同步记录\
        """
        shop_obj = self.pool.get('ebiz.shop')
        shop = shop_obj.browse(cr, uid, shop_id, context=context)
        location_id = shop.warehouse_id.lot_stock_id.id
        # 计算库存是增量还是减量
        product_qty = product_qty if location_id == dest_location_id else -product_qty
        vals = {
            'shop_id': shop_id,
            'location_id': location_id,
            'product_id': product_id,
            'sync_check': True
        }
        ids = self.search(cr, uid, [('shop_id', '=', shop_id), ('location_id', '=', location_id),
                                    ('product_id', '=', product_id), ('sync_check', '=', True)], context=context)
        if ids:
            self.write(cr, uid, ids, vals, context=context)
            for s in self.read(cr, uid, ids, ['var_qty'], context=context):
                self.write(cr, uid, [s['id']], {'var_qty': s['var_qty'] + product_qty}, context=context)
        else:
            vals.update({'var_qty': product_qty})
            self.create(cr, uid, vals, context=context)

        return True

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
            product_lines.append({
                'sku_guid':guid,
                'sku_id':ebiz_stock['id'],
                'sync_qty':ebiz_stock['var_qty'],
                'storage_guid':seller.stock_warehouse_id.id and str(seller.stock_warehouse_id.id) or '',
                'storage_name':seller.stock_warehouse_id.name or '',
                'storage_alias':seller.stock_warehouse_id.code or '',
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
            product_lines.append({
                'sku_guid':guid,
                'sku_id':ebiz_stock['id'],
                'sync_qty':ebiz_stock['stock_qty'],
                'storage_guid':seller.stock_warehouse_id.id and str(seller.stock_warehouse_id.id) or '',
                'storage_name':seller.stock_warehouse_id.name or '',
                'storage_alias':seller.stock_warehouse_id.code or '',
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

    def auto_sync_var(self, cr, uid, ids, context=None):
        todo_ids = self.search(cr, uid, [('var_qty','!=',0),('sync_check','!=',False)])
        self.sync_stock_var(cr, uid, todo_ids, context=context)
        return True

SYNC_ERR_TYPES = [('product', u'商品同步'), ('order', u'订单同步'), ('stock', u'库存同步'),
                  ('delivery', u'运单同步'), ('invoice', u'发票/对账单同步'), ]


class ebiz_syncerr(models.Model):
    _name = 'ebiz.syncerr'
    _description = u"电商同步异常"
    _order = "id desc"

    create_date = fields.Datetime(u'时间', readony=True)
    name = fields.Text(u'错误描述', required=True, readony=True)
    shop_id = fields.Many2one('ebiz.shop', string=u"店铺", required=True, readony=True)
    type = fields.Selection(SYNC_ERR_TYPES, u'错误类型', required=True, readony=True)
    state = fields.Selection([('draft', u'未解决'), ('done', u'已解决'), ], u'错误状态', default='draft', required=True,
                             readony=True)

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True


class ebiz_message(models.Model):
    _name = 'ebiz.message'
    _description = u"短信发送接口"
    _order = "id desc"

    phone = fields.Char(u'手机号码', )
    create_date = fields.Datetime(u'创建时间', readony=True)
    write_date = fields.Datetime(u'最后发送时间', readony=True)
    name = fields.Text(u'短信内容', required=True, )
    state = fields.Selection([('draft', u'待发送'), ('done', u'已发送'), ('error', u'发送失败'), ], u'发送状态',
                             required=True, readony=True, default='draft')

