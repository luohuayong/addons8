# -*- coding: utf-8 -*- #

import time
from openerp.osv import osv, fields
import logging

logger = logging.getLogger(__name__)

class delivery_order_print(osv.osv_memory):

    _inherit = 'delivery.order.print'

    def print_logistics_interface_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids',[])
        sequence_model = self.pool['ir.sequence']
        picking_model = self.pool['stock.picking']
        selftake_carrier = self.pool['ir.model.data']\
        .get_object_reference(cr, uid, 'bysun_delivery_V2', 'stock_picking_selftake_carrier')[1]
        for picking in picking_model.browse(cr, uid, active_ids):
            if (picking.carrier_id and picking.carrier_id.id or -1) == selftake_carrier:
                sequnce = sequence_model.get(cr, uid, 'bysun.picking.selftake', context=context)
                for other_picking in picking.sale_id.picking_ids:
                    if other_picking.picking_type_code in ('internal','outgoing'):
                        other_picking.write({'carrier_tracking_ref':sequnce})
                active_ids.remove(picking.id)
        if active_ids:
            ctx = context.copy()
            ctx.update({'active_ids':active_ids,'active_id':active_ids[0]})
            return super(delivery_order_print,self).print_logistics_interface_order(cr, uid, ids, context=ctx)
        return True