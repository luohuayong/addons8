    # -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from openerp.tools.translate import _
from openerp.osv import osv, orm, fields
from openerp import SUPERUSER_ID
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)
class stock_production(osv.osv):
    _name = 'stock.production'
    _description = u'仓库加工单'
    
    _columns = {
        'name':fields.char(u'单号',states={'confirm': [('readonly', True)]}),
        'processing_date':fields.date(u'操作日期',states={'confirm': [('readonly', True)]}),
        'create_uid':fields.many2one('res.users',u'操作人',states={'confirm': [('readonly', True)]}),
        'stock_lot':fields.many2one('stock.production.lot',u'成品批次号'),
        'write_uid':fields.many2one('res.users',u'发起人',states={'confirm': [('readonly', True)]}),
        'product_id':fields.many2one('product.product',u'产成品',required=True,states={'confirm': [('readonly', True)]}),
        'product_uom_qty':fields.float(u'数量',required=True,states={'confirm': [('readonly', True)]}),
        'product_uom':fields.many2one('product.uom',u'单位',required=True,states={'confirm': [('readonly', True)]}),
        'warehouse_id': fields.many2one('stock.warehouse', u'仓库', required=True,states={'confirm': [('readonly', True)]}),
        'processing_type':fields.selection([('one2many',u'一对多'), ('many2one', u'多对一')], u'加工类型'),
        'state':fields.selection([('draft', u'草稿'), ('confirm', u'完成'),('cancel', u'取消')], u'状态'),
        'product_lines':fields.one2many('stock.production.line','product_order','Product lines',states={'confirm': [('readonly', True)]}), 
        }
        
    _defaults = {
        'state':'draft',
        'processing_date':lambda *a: time.strftime('%Y-%m-%d'), 
        'create_uid':lambda self, cr, uid, context: uid,
    }

    # _sql_constraints = [
    #     ('stock_lot_uniq', 'unique (stock_lot)', u'产成品的序列号不能重复!')
    # ]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not vals.get('name', ''):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, "stock.production")
        return super(stock_production, self).create(cr, uid, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.production'),
        })
        return super(stock_production, self).copy(cr, uid, id, default, context=context)

    def unlink(self, cr, uid, ids, context=None):
        stock_productions = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in stock_productions:
            if s['state'] in ['draft', 'cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(u"无效!", u"已经完成的单据是不能删除的!")
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    def act_cancel(self, cr, uid, ids, context=None):
        # cancel_stocks = self.read(cr, uid, ids, ['state'], context=context)
        # unlink_ids = []
        # for s in cancel_stocks:
        #     if s['state'] in ['draft', 'cancel']:
        #         unlink_ids.append(s['id'])
        #     else:
        #         raise osv.except_osv(u"无效!", u"已经完成的单据是不能删除的!")
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def _get_picking_type(self, cr, uid, warehouse_id, in_out = 'incoming', context=None):
        type_obj = self.pool.get('stock.picking.type')
        types = type_obj.search(cr, uid, [('code', '=', in_out), ('warehouse_id', '=', warehouse_id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', in_out), ('warehouse_id', '=', False)], context=context)
            if not types:
                raise osv.except_osv(u"错误", u"请确认该仓库定义了出/入库单类型!" )
        return types[0]

    def raw_picking_done(self, cr, uid, production, context=None):
        """为加工单创建原料出库单，并自动出库
        """
        pick_obj = self.pool.get("stock.picking")
        move_obj = self.pool.get("stock.move")
        
        picking_type_id = self._get_picking_type(cr, uid, production.warehouse_id.id, 'outgoing', context = context)
        picking_vals = {
            'picking_type_id': picking_type_id,
            'date': production.processing_date or time.strftime('%Y-%m-%d'),
            'date_done': production.processing_date or time.strftime('%Y-%m-%d'),
            'origin': production.name
        }
        picking_id = pick_obj.create(cr, uid, picking_vals, context=context)
        if production.processing_type == 'many2one':
            for line in production.product_lines:
                move_obj.create(cr, uid, {
                    'picking_id': picking_id, 
                    'product_id': line.product_id and line.product_id.id or False,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom and line.product_uom.id or False,
                    'name': line.product_id.name,
                    'origin': production.name or '',
                    'location_id': production.warehouse_id.lot_stock_id.id,
                    'location_dest_id': line.product_id.property_stock_production.id ,  
                    'invoice_state': 'none',
                    'restrict_lot_id':line.stock_lot and line.stock_lot.id or False,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                }, context=context)

        if production.processing_type == "one2many":
            move_obj.create(cr, uid, {
                    'picking_id': picking_id, 
                    'product_id': production.product_id and production.product_id.id or False,
                    'name': production.product_id.name,
                    'origin': production.name or '',
                    'product_uom_qty': production.product_uom_qty,
                    'product_uom': production.product_uom and production.product_uom.id or False,
                    'location_id': production.warehouse_id.lot_stock_id.id, 
                    'location_dest_id': production.product_id.property_stock_production.id, 
                    'invoice_state': 'none',
                    'restrict_lot_id':production.stock_lot and production.stock_lot.id or False,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                }, context=context)
        
        #Picking自动锁货，自动出库
        pick_obj.action_assign(cr, uid, [picking_id], context = context )
        transfer_model = self.pool['stock.transfer_details']
        ctx = context.copy()
        ctx.update({'active_id':picking_id,'active_model':'stock.picking','active_ids':[picking_id]})
        created_id = transfer_model.create(cr, uid, {'picking_id': picking_id or False}, ctx)
        # transfer_model.do_detailed_transfer(cr, uid, created_id, context=ctx)
        # pick_obj.action_done(cr, uid, [picking_id], context = context )
        pick_obj.do_transfer(cr, uid, [picking_id], context=context)
        
        return picking_id
        
    def product_picking_done(self, cr, uid, production, raw_picking_id, context=None):
        """
        1) 计算加工单的原料成品，分摊到成品成本
        2) 为加工单创建成品入库单，并自动入库
        """
        pick_obj = self.pool.get("stock.picking")
        move_obj = self.pool.get("stock.move")
        
        picking_type_id = self._get_picking_type(cr, uid, production.warehouse_id.id, 'incoming', context = context)
        picking_vals = {
            'picking_type_id': picking_type_id,
            'date': production.processing_date or time.strftime('%Y-%m-%d'),
            'date_done': production.processing_date or time.strftime('%Y-%m-%d'),
            'origin': production.name
        }
        picking_id = pick_obj.create(cr, uid, picking_vals, context=context)
        
        raw_cost = 0.0
        for sm in pick_obj.browse(cr, uid, raw_picking_id, context = context ).move_lines :
            raw_cost += sm.product_uom_qty * sm.price_unit
        
        product_lot = {}
        if production.processing_type == 'many2one':
            price_unit = raw_cost / production.product_uom_qty
            move_obj.create(cr, uid, {
                    'picking_id': picking_id, 
                    'product_id': production.product_id and production.product_id.id or False,
                    'name': production.product_id.name,
                    'origin': production.name or '',
                    'price_unit': price_unit,
                    'product_uom_qty': production.product_uom_qty,
                    'product_uom': production.product_uom and production.product_uom.id or False,
                    'location_id': production.product_id.property_stock_production.id,  
                    'location_dest_id': production.warehouse_id.lot_stock_id.id,  
                    'invoice_state': 'none',
                    # 'restrict_lot_id':production.stock_lot and production.stock_lot.id or False,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    }, context=context)
            product_lot.update({
                    production.product_id and production.product_id.id or False:production.stock_lot and production.stock_lot.id or False,
                })
        if production.processing_type == "one2many":
            total_price = 0.0
            for line in production.product_lines:
                sale_price = line.product_id.lst_price or 1.0
                total_price += line.product_uom_qty * sale_price
                
            price_unit = raw_cost / total_price
            for line in production.product_lines:
                move_obj.create(cr, uid, {
                    'picking_id': picking_id, 
                    'product_id': line.product_id.id,
                    'price_unit': price_unit * (line.product_id.lst_price or 1.0),
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom and line.product_uom.id or False,
                    'name': line.product_id.name,
                    # 'restrict_lot_id':line.stock_lot and line.stock_lot.id or False,
                    'origin': production.name or '',
                    'location_id': line.product_id.property_stock_production.id,
                    'location_dest_id': production.warehouse_id.lot_stock_id.id,  
                    'invoice_state': 'none',
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                }, context=context)

                product_lot.update({
                    line.product_id.id:line.stock_lot and line.stock_lot.id or False,
                })

        #Picking自动锁货，自动出库
        pick_obj.action_assign(cr, uid, [picking_id], context = context )
        transfer_model = self.pool['stock.transfer_details']
        ctx = context.copy()
        ctx.update({'active_id':picking_id,'active_model':'stock.picking','active_ids':[picking_id]})
        created_id = transfer_model.create(cr, uid, {'picking_id': picking_id or False}, ctx)
        operation_model = self.pool['stock.pack.operation']
        operation_to_done = []
        for product in product_lot:
            operation_ids = operation_model.search(cr, uid, [('product_id','=',product),('picking_id','=',picking_id),('processed','=','false')])
            if operation_ids:
                operation_model.write(cr, uid, operation_ids, {'lot_id':product_lot.get(product,False)})
                operation_to_done.extend(operation_ids)
        # operation_model.action_drop_down(cr, uid, operation_to_done, context=context)

        # transfer_model.do_detailed_transfer(cr, uid, created_id, context=ctx)
        # pick_obj.action_done(cr, uid, [picking_id], context = context)
        pick_obj.do_transfer(cr, uid, [picking_id], context = context)
        
        return picking_id

    def act_confirm(self, cr, uid, ids, context=None):
        """加工单确认，系统自动完成下述动作：
        1）生成原料出库单，自动锁货，自动出库
        2）根据原料出库单，自动计算原料总成本，并按成品销售价格分摊到成品成本
        3）生成成品入库单，自动入库
        """
        quant_obj = self.pool.get('stock.quant')
        location_obj = self.pool.get('stock.location')

        for production in self.browse(cr, uid, ids, context = context):
            if production.product_uom_qty <= 0.0:
                raise osv.except_osv(_('错误!'),_('不能确认成品小于等于0的加工单.'))
            if not production.product_lines:
                raise osv.except_osv(_('错误!'),_('不能确认没有明细行的加工单.'))
            production.write({'state':'confirm'})
            for line in production.product_lines:
                if line.product_uom_qty <= 0.0:
                    raise osv.except_osv(_('错误!'),_('不能确认原料小于等于0的加工单.'))
        self.write(cr,uid,ids,{'state':'confirm'}, context=context)
        raw_picking_id = self.raw_picking_done(cr, uid, production, context = context)
        picking_id = self.product_picking_done(cr, uid, production, raw_picking_id, context = context)
        return True

    def onchange_product_id(self, cr, uid, ids, product_id, product_uom_qty, processing_type, warehouse_id, context=None):
        if context is None:
            context = {}
        res = {}
        if product_id:
            product = self.pool['product.product'].browse(cr, uid, product_id, context)
            res.update({'value':{'product_uom':product.uom_id.id}})
            if not warehouse_id:
                res.update({'warning':{'title':u'错误','message':u'请先选择仓库'},'value':{'product_id':False,'product_uom':False}})
            else:
                if processing_type == 'one2many' and product_uom_qty:
                    warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
                    ctx = context.copy()
                    ctx.update({'location':[warehouse.lot_stock_id.id]})
                    product = self.pool.get('product.product').read(cr, uid, product_id, ['sale_available'], context=ctx)
                    if product['sale_available'] < product_uom_qty:res.update({'warning':{'title':u'错误','message':u'选择的原材料库存不足'},\
                        'value':{'product_id':False,'product_uom':False,'product_uom_qty':0}})
        return res

class stock_production_line(osv.osv):
    _name = 'stock.production.line'
    _columns = {
        'product_order':fields.many2one('stock.production',u'加工单ID'),
        'product_id':fields.many2one('product.product', u'原料',required=True),
        'stock_lot':fields.many2one('stock.production.lot',u'批次号'),
        'product_uom_qty':fields.float(u'数量', required=True),
        'product_uom':fields.many2one('product.uom', u'单位',required=True),
        'state':fields.selection([('draft', u'草稿'), ('confirm', u'完成')], u'状态'),
    }
    _defaults = {
    
    }
    
    def onchange_line_product_id(self, cr, uid, ids, product_id, product_uom_qty, processing_type, warehouse_id, context=None):
        if context is None:
            context = {}
        res = {}
        if product_id:
            product = self.pool['product.product'].browse(cr, uid, product_id, context)
            res.update({'value':{'product_uom':product.uom_id.id}})
            if not warehouse_id:
                res.update({'warning':{'title':u'错误','message':u'请先选择仓库'},'value':{'product_id':False,'product_uom':False}})
            else:
                if processing_type == 'many2one' and product_uom_qty:
                    warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
                    ctx = context.copy()
                    ctx.update({'location':[warehouse.lot_stock_id.id]})
                    product = self.pool.get('product.product').read(cr, uid, product_id, ['sale_available'], context=ctx)
                    if product['sale_available'] < product_uom_qty:res.update({'warning':{'title':u'错误','message':u'选择的原材料库存不足'},\
                        'value':{'product_id':False,'product_uom':False,'product_uom_qty':0}})
        return res

