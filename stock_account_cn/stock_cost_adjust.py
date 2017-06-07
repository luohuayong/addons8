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

        #检索信息，并添加到reason中，格式：库位 数量 变动金额
        product_id=adjust_obj.product_id.id
        cr.execute("""select d.complete_name as location_name,
                               sum(c.qty) as product_qty,
                               to_char(e.date_done,'yyyy-mm') as date_done
                            from stock_move as a
                            left join stock_quant_move_rel as b on
                                      a.id=b.move_id
                            left join stock_quant as c on
                                      c.id=b.quant_id
                            left join stock_location as d on
                                      c.location_id=d.id
                            left join stock_picking as e on
                                      a.picking_id=e.id
                            where b.move_id = %s
                            and c.product_id = %s
                            and c.location_id not in(7,12,721,715)
                            group by d.complete_name,c.product_id,date_done
                            order by location_name""",
                            [move_id,product_id]
                            )
        if cr.rowcount:
            product_location_list=u'\n\n库位，数量，变动金额，出入库月份\n'
            res3 = cr.fetchall()
            for x in res3:
                location=x[0].split(' / ')
                location.pop(0)
                new_location_path=''
                for new_location in location:
                    new_location_path = new_location_path + ' / ' + new_location
                new_location_path=new_location_path[3:]
                price = x[1] * (round(adjust_obj.new_cost, 2) - round(adjust_obj.origin_cost, 2))
                product_location_infos = new_location_path + ',' + str(x[1]) + ',' + str(price) + ',' + str(x[2]) + '\n'
                product_location_list = product_location_list + product_location_infos

            reason=adjust_obj.reason+product_location_list
            self.write(cr, uid, ids[0], {'reason': reason}, context=context)

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


