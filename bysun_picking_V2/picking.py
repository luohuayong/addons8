# -*- encoding: utf-8 -*-
import time
from openerp import pooler
import logging
import traceback
import json
from openerp.tools.translate import _
from openerp import tools,api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from openerp.osv import fields,osv

_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'infact_weight':fields.float(u'实际重量'),
    }

    _defaults = {
        'infact_weight':0.00,
    }

class stock_pack_operation(osv.osv):
    _inherit = "stock.pack.operation"

    def action_drop_down2(self, cr, uid, ids, qty_done, weight=0,context=None):
        stock_model = self.pool['stock.picking']
        sale_logistic = self.pool['sale.order.logistic']
        for id in ids:
            self.write(cr, uid, id, {'qty_done': qty_done[str(id)] }, context=context)
        res = self.action_drop_down(cr, uid, ids, context=context)
        sync_picking_ids = []
        picking_weight = []
        for op in self.browse(cr, uid, ids, context=context):
            if not op.picking_id.sale_id:continue
            unprocessed = self.search(cr, uid, [('processed','=','false'),('picking_id','=',op.picking_id.id)])
            if not unprocessed:
                sync_picking_ids.append(op.picking_id.sale_id.id)
            picking_weight.append(op.picking_id)
            #往出运单上写重量 
            picking = self.pool.get('stock.picking').browse(cr, uid, op.picking_id.id, context=context)
        if picking_weight:
            for pick_weight in set(picking_weight):
                if op.picking_id.sale_id:
                    for picking_id in op.picking_id.sale_id.picking_ids:
                        if picking_id.picking_type_code != 'incoming':
                            picking_id.write({'infact_weight':picking_id.infact_weight + float(weight)})
                            # cr.execute('update stock_picking set weight=%s where id= %s', (picking_id.weight + float(weight), picking_id.id,))
                else:
                    pick_weight.write({'infact_weight':pick_weight.infact_weight + float(weight)})
                    # cr.execute('update stock_picking set weight=%s where id= %s', (picking_id.weight + float(weight), picking_id.id,))
                # cr.execute('update stock_picking set weight=%s where id= %s', (weight, op.picking_id.id,))           
        if sync_picking_ids:
            for sale in set(sync_picking_ids):
                sale_logistic.create(cr, uid, {
                        'name': 'package',
                        'user_id': uid,
                        'order_id': sale,
                        'state':'draft',
                        'memo':u'打包',
                        })
        return res