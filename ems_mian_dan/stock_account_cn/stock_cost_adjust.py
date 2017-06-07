# -*- coding: utf-8 -*- #
from openerp import tools
from openerp.osv import osv, fields
import logging
import time
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class stock_cost_adjust(osv.osv):
    _name = 'stock.cost.adjust'

    _columns = {
        'name':fields.char(u'单号',readonly=True),
        'user_id':fields.many2one('res.users',u'调整人',states={'done': [('readonly', True)]}),
        'ca_date':fields.datetime(u'调整时间',states={'done': [('readonly', True)]}),
        'product_id':fields.many2one('product.product',u'存货产品',required=True,states={'done': [('readonly', True)]}),
        'move_id': fields.many2one('stock.move', u'入库明细',states={'done': [('readonly', True)]}),
        'origin_cost': fields.float(u'调整前价格',states={'done': [('readonly', True)]}),
        'new_cost':fields.float(u'调整后价格',required=True,states={'done': [('readonly', True)]}),
        'reason':fields.text(u'调整原因',required=True,states={'done': [('readonly', True)]}),
        'state':fields.selection([('draft', u'草稿'), ('done', u'完成')], u'状态'),
    }
    _defaults = {
        'user_id':lambda self, cr, uid, context: uid,
        'ca_date':lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), 
        'state': 'draft', 
    }  

    def onchange_origin_cost(self, cr, uid, ids,move_id,context=None):
        res = {'value': {'origin_cost':0.0}}
        if move_id:
            price = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
            res['value']['origin_cost'] = price.price_unit
        return res

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not vals.get('name', ''):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, "stock.cost.adjust")
        return super(stock_cost_adjust, self).create(cr, uid, vals, context=context)

    def confirm_button(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        adjust_obj = self.browse(cr, uid, ids[0], context=context)
        move_id = adjust_obj.move_id.id
        self.write(cr, uid, ids, {'state':'done'})
        return self.pool.get('stock.move').adjust_price(cr, uid, [move_id], adjust_obj.new_cost,context=context)
        
 
class stock_move(osv.osv):
    _inherit = 'stock.move'
    def adjust_price(self, cr, uid, ids, new_cost, context=None):
        """
        系统自动更新该Stock Move的价格，以及Stock Quants的价格，
        以及从该Stock Quants出库的所有Stock Move及Stock Quants的成本价格。
        """
        if context is None:
            context = {}
        quants_todo = []
        move_todo = []
        for move_id in ids:
            cr.execute("select quant_id from stock_quant_move_rel where move_id = %s", (move_id,))
            res = cr.fetchall()
            quants_todo += [x[0] for x in res]
            for quant_id in quants_todo:
                cr.execute("select move_id from stock_quant_move_rel where quant_id = %s", (quant_id,))
                res2 = cr.fetchall()
                move_ids = [x[0] for x in res2]
                move_ids.sort()
                idx = move_ids.index(move_id)
                if idx >= 0:
                    move_todo += move_ids[idx:]
        self.write(cr, uid, [x for x in set(move_todo)], {'price_unit': new_cost})
        self.pool.get('stock.quant').write(cr, uid, [x for x in set(quants_todo)], {'cost': new_cost})
        return True


