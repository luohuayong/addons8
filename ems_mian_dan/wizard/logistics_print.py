# -*- coding: utf-8 -*- #

import time
from openerp.osv import osv, fields
import logging

logger = logging.getLogger(__name__)

class delivery_order_print(osv.osv_memory):

    _inherit = 'delivery.order.print'

    def print_ems_logistics_interface_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        shop_model = self.pool['ebiz.shop']
        stock_picking = self.pool['stock.picking']
        ems_model = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'ems_mian_dan', 'stock_picking_ems_carrier')
        ems_carrier = ems_model and ems_model[1] or False
        active_ids = context.get('active_ids', [])
        success_picking = []
        for picking_read in stock_picking.read(cr, uid, active_ids, ['carrier_tracking_ref']):
            if picking_read.get('carrier_tracking_ref',''):
                success_picking.append(picking_read.get('id'))
                active_ids.remove(picking_read.get('id'))
        post_vals = self.pool['stock.picking'].prepare_ems_logistics_interface_order(cr, uid, active_ids)
        fail_picking = ''
        for post_val in post_vals:
            res = shop_model.remote_ems_logistics_call(cr, uid, post_vals.get(post_val)[0], context=context)
            picking = stock_picking.browse(cr, uid, post_val)
            if res.get('result','') == 'success':
                success_picking.append(post_val)
                post_vals.get(post_val)[1].write({'state':'used','sale_id':picking.sale_id.id})
                for same_picking in picking.sale_id.picking_ids:
                    if same_picking.state != 'cancel' and same_picking.picking_type_code != 'incoming':
                        same_picking.write({'carrier_tracking_ref':post_vals.get(post_val)[1].number,'carrier_id':ems_carrier})
            elif res.get('result','') == 'fail':
                fail_picking += '%s:%s\n'%(picking.name,res.get('err_msg',''))
        logger.info(fail_picking)
        if not success_picking:
            raise osv.except_osv('Warning !', fail_picking)
        else:
            context.update({
                'active_id':success_picking[0],
                'active_ids':success_picking,
                })
            return {
                'type':'ir.actions.report.xml',
                'report_type':'qweb-pdf',
                'report_name':'ems_mian_dan.ems_logistics',
                'context':context,
            }

class ems_carrier_tracking_ref_wizard(osv.osv_memory):
    _name = "ems.carrier.tracking.ref.wizard"
    _description = u"快速创建快递单号"

    _columns = {
        'start_no':fields.char(u'起始单号'),
        'end_no':fields.char(u'结束单号'),
    }

    def quickly_create_ems_no(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0])
        ems_no_model = self.pool['ems.carrier.tracking.ref']
        for i in range(int(wizard.start_no),int(wizard.end_no) + 1):
            ems_no_model.create(cr, uid, {
                    'number':str(i),
                    'sale_id':False,
                    'state':'no_use',
                })
        return True
