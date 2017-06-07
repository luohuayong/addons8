# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.osv import osv
import logging
# import uuid
from datetime import datetime

_logger = logging.getLogger(__name__)
DOMESTIC_IMPORT = [('in',u'国产'),('out',u'进口')]

class product_brand(models.Model):
    _name = 'product.brand'

    bran_desc = fields.Char(u'品牌说明')
    name = fields.Char(u'名字')

class product_product(models.Model):
    _inherit = 'product.product'

    guid = fields.Char(string=u'SKU编码',copy=False)
    market_price = fields.Float(u'市场价')

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not vals.get('guid',''):
            vals['guid'] = self.pool.get('ir.sequence').get(cr, uid, 'product.product')
        return super(product_product, self).create(cr, uid, vals, context=context)

    def onchange_uom_type(self, cr, uid, ids, uom_type, context=None):
        res = {'value':{}}
        res['value'] = {'uom_id':False,'uom_po_id':False}
        return res

    def action_sync_qty(self, cr, uid, ids, context=None):
        ebiz_stock_model = self.pool['ebiz.stock']
        ebiz_shop_model = self.pool['ebiz.shop']
        partner_model = self.pool['res.partner']
        warehouse_model = self.pool['stock.warehouse']
        if not isinstance(ids,list):
            ids = [ids]
        ebiz_stock_ids = []
        for product in self.read(cr, uid, ids, ['virtual_available','incoming_qty','seller_id'], context=context):
            exist_id = ebiz_stock_model.search(cr, uid, [('var_qty','=',0),('sync_check','=',True),('product_id','=',product['id'])])
            if exist_id:
                ebiz_stock_model.write(cr, uid, exist_id, {'stock_qty':product['virtual_available'] - product['incoming_qty']})
                ebiz_stock_ids += exist_id
            else:
                seller_id = product['seller_id'] and product['seller_id'][0] or False
                partner_id = partner_model.read(cr, uid, seller_id, ['stock_warehouse_id']) or {}
                warehouse_id = partner_id.get('stock_warehouse_id',False) and partner_id['stock_warehouse_id'][0] or False
                location_id = warehouse_model.read(cr, uid, warehouse_id, ['lot_stock_id']) or {}
                location_id = location_id.get('stock_loc_id',False) and location_id['stock_loc_id'][0] or 1
                ebiz_shop = ebiz_shop_model.search(cr, uid, [])
                ebiz_stock_id = ebiz_stock_model.create(cr, uid, {
                    'shop_id':ebiz_shop and ebiz_shop[0] or False,
                    'location_id':location_id,
                    'sync_check':True,
                    'stock_qty':product['virtual_available'] - product['incoming_qty'],
                    'product_id':product['id'],
                    })
                ebiz_stock_ids.append(ebiz_stock_id)
        return ebiz_stock_ids

class product_template(models.Model):
    _inherit = 'product.template'

    temp_zone = fields.Char(string=u'储存方式')
    t_guid = fields.Char(string=u'商品编码',copy=False)
    package = fields.Char(u'包装')
    place_of_origin = fields.Char(u'产地')
    content_net = fields.Char(u'净含量')
    # weight_net = fields.Integer(u'净重')
    uom_type = fields.Many2one('product.uom.categ',u'产品单位类型')
    brand_id = fields.Many2one('product.brand', u'品牌')
    special_flag1 = fields.Many2one('product.flag', u'特殊标记')
    product_psn = fields.Char(u'产品货号')
    packing_sizes = fields.Char(u'包装尺寸')
    component_specification = fields.Char(u'件装规格')
    component_unit = fields.Char(u'件装单位')
    sync_date = fields.Datetime(u'同步时间', copy=False)
    component_number = fields.Char(u'件装数')
    variety = fields.Char(u'品种')
    seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id', 'Supplier', copy=True)
    domestic_import = fields.Selection(DOMESTIC_IMPORT, u'国别')
    organtic_food = fields.Selection([('y',u'是'),('n',u'否')], u'是否有机食品')
    product_standard_no = fields.Char(u'产品标准号(QS)')
    production_license_no = fields.Char(u'生产许可证编号')

    _order = "write_date desc"

    _defaults = {
        'track_all':True,
        'categ_id': False,
        'type':'product',
    }

    def onchange_uom_type(self, cr, uid, ids, uom_type, context=None):
        res = {'value':{}}
        res['value'] = {'uom_id':False,'uom_po_id':False}
        return res

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not vals.get('t_guid',''):
            vals['t_guid'] = self.pool.get('ir.sequence').get(cr, uid, 'product.product')
        return super(product_template, self).create(cr, uid, vals, context=context)

    def _get_attributes_string(self, cr, uid, p, context=None):
        product_skus = []
        for pp in p.product_variant_ids:
            if not pp.active:continue
            variants = ''
            for pa in pp.attribute_value_ids:
                variants += "%s:%s;"%(pa.attribute_id.name,pa.name)
            variants = variants[:-1].split(';')
            variants.sort()
            variants_sort = ''
            for variant in variants:
                variants_sort += "%s;"%(variant)
            variants_sort = variants_sort[:-1]
            _logger.info(variants_sort)
            product_skus.append({
                'sku_guid':pp.guid or '',
                'variant':variants_sort or '',
                'sales_price':pp.lst_price,
                'market_price':pp.market_price,
                'cost_price':pp.standard_price,
                })
        return product_skus

    def _get_write_date(self, cr, uid, p, context=None):
        write_date = [p.write_date]
        for pp in p.product_variant_ids:
            if not pp.active:continue
            write_date.append(pp.write_date)
        write_date.sort()
        return write_date[-1]

    def _prepare_sync_vals(self, cr, uid, p, context=None):
        # temps = {'N': u'常温', 'C': u'冷藏', 'F': u'冷冻'}
        domestic = {'in':u'国产','out':u'进口'}
        organtic_food = {'y':u'是','n':u'否'}
        supplier = p.seller_id or False
        product_skus = self._get_attributes_string(cr, uid, p, context=context)
        write_date = self._get_write_date(cr, uid, p, context=context)
        product = {
            'product_guid': p.t_guid or '',
            'product_psn': p.product_psn or '',
            'pack':p.package or '',
            'supplier_id':supplier and supplier.guid or '',
            'supplier_name':supplier and supplier.name or '',
            'brand_guid':p.brand_id and p.brand_id.id or False,
            'production':p.place_of_origin or '',
            'content':p.content_net or '',
            'type':p.categ_id.name_get()[0][1],
            'suttle':p.weight_net or 0.00,
            'name': p.name or '',
            'brand':p.brand_id and p.brand_id.name or '',
            'bran_desc': p.brand_id and p.brand_id.bran_desc or '',
            'life_time': p.life_time and str(p.life_time) or '',
            'unit': p.uom_id and p.uom_id.name or '',
            'storage_condition': p.temp_zone,
            'ean13':p.ean13 or '',
            'special_flag':p.special_flag1 and p.special_flag1.flag or 0,
            'packing_sizes':p.packing_sizes or '',
            'component_specification':p.component_specification or '',
            'component_unit':p.component_unit or '',
            'variety':p.variety or '',
            'domestic_import':domestic.get(p.domestic_import, ''),
            'organic_food':organtic_food.get(p.organtic_food, ''),
            'product_standard_no':p.product_standard_no or '',
            'production_license_no':p.production_license_no or '',
            'component_number':p.component_number or '',
            'product_skus':product_skus,
            'write_date':write_date,
        }
        return product


    def sync_product(self, cr, uid, ids, context=None):
        _logger.info("syncing product")
        shop_obj = self.pool.get('ebiz.shop')
        result = {}
        now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in self.browse(cr, uid, ids, context=context):
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

class product_attribute_line(models.Model):
    _inherit = 'product.attribute.line'

    def onchange_attribute_id(self, cr, uid, ids, context=None):
        return {'value':{'value_ids':[]}}

class product_flag(models.Model):
    _name = 'product.flag'

    name = fields.Char(u'值')
    flag = fields.Char(u'标记值')