# -*- coding: utf-8 -*- #

import time
from openerp.osv import osv, fields
import logging

logger = logging.getLogger(__name__)

class delivery_order_print(osv.osv_memory):

    _inherit = 'delivery.order.print'

    _columns = {
        'start_carrier_seq': fields.char(u'起始单号'),
        'end_carrier_seq': fields.char(u'结束单号'),
        'order_count': fields.integer(u'待打印数' ),
    }
    _defaults = {
        'start_carrier_seq':'0',
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        carrier = self.pool['delivery.carrier']
        stock_model = self.pool['stock.picking']
        res = super(delivery_order_print,self).default_get(cr, uid, fields, context=context)
        order_count = context.get('active_ids',False)
        if order_count:
            carrier_id = stock_model.read(cr, uid, order_count[0], ['carrier_id'])
            if carrier_id['carrier_id']:
                next_sequence = carrier.read(cr, uid, carrier_id['carrier_id'][0], ['next_sequence'])
                res.update({'start_carrier_seq':next_sequence['next_sequence']})
        res.update({'order_count':len(order_count)})
        return res

    def close_clear(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def print_logistics_interface_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        shop_model = self.pool['ebiz.shop']
        stock_picking = self.pool['stock.picking']
        # raise osv.except_osv('Warning !', u'快递单格式开发中!')
        active_ids = context.get('active_ids', [])
        post_vals = self.pool['stock.picking'].prepare_logistics_interface_order(cr, uid, active_ids)
        success_picking = []
        fail_picking = ''
        for post_val in post_vals:
            res = shop_model.remote_logistics_call(cr, uid, post_vals.get(post_val), context=context)
            picking = stock_picking.browse(cr, uid, post_val)
            if res.get('result','') == 'success':
                success_picking.append(post_val)
                for same_picking in picking.sale_id.picking_ids:
                    if same_picking.state != 'cancel' and same_picking.picking_type_code != 'incoming':
                        same_picking.write({'carrier_tracking_ref':res.get('mailNo',''),'sanduan_code':res.get('shortAddress','')})
            elif res.get('result','') == 'fail':
                fail_picking += '%s:%s\n'%(picking.name,res.get('err_msg',''))

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
                'report_name':'bysun_delivery.yt_logistics',
                'context':context,
            }
 
    def print_kuaidi(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # raise osv.except_osv('Warning !', u'快递单格式开发中!')
        active_ids = context.get('active_ids', [])
        pack_model = self.pool['stock.quant.package']
        cr.execute('select distinct carrier_id from stock_picking where id in %s', (tuple(active_ids),))
        carrier_ids = cr.fetchall()
        if len(carrier_ids) > 1:
            raise osv.except_osv('Warning !', u'请选择相同快递公司的发货单再行处理!')
        if not carrier_ids[0][0]:
            raise osv.except_osv('Warning !', u'请确认所选发货单已填写快递公司再行处理!')
        res = self.read(cr, uid, ids, ['start_carrier_seq','end_carrier_seq','order_count'], context=context)
        start = res and res[0]['start_carrier_seq'] or False
        end = res and res[0]['end_carrier_seq'] or None
        try:
            if start:
                int(start)
            if end:
                int(end)
        except Exception, e:
            raise osv.except_osv('Warning !', u'起始单号和结束单号必须为纯数字!')
        cnt = res and res[0]['order_count'] or 1
        if not start:
            raise osv.except_osv('Warning !', u'必须输入起始单号！')

        carrier_obj = self.pool.get('delivery.carrier')
        pick_obj = self.pool.get('stock.picking')
        carrier = pick_obj.read(cr, uid, active_ids[0], ['carrier_id'])
        if cnt > len(active_ids): cnt = len(active_ids)
        seq_list = carrier_obj.generate_seq(cr, uid, carrier['carrier_id'][0], start, cnt + 1, end)
        report_id = carrier_obj.read(cr, uid, carrier['carrier_id'][0], ['report_id'])
        carrier_obj.write(cr, uid, carrier['carrier_id'][0], {'next_sequence':seq_list[-1]})
        if not report_id['report_id']:
            raise osv.except_osv('Warning !', u'请设置快递公司的面单格式!')
        report_name = self.pool['ir.actions.report.xml'].read(cr, uid, report_id['report_id'][0], ['report_name'])
        for i in range(len(seq_list) - 1):
            #快递单号写入该SO的所有未完的Stock Picking
            group_id = pick_obj.read(cr, uid, active_ids[i], ['group_id'] )
            pick_ids = pick_obj.search(cr, uid, [('group_id' ,'=', group_id['group_id'][0]), ('state','not in', ['cancel', 'done'] ) ] )
            if pick_ids:
                pick_obj.write(cr, uid, pick_ids, {'carrier_tracking_ref':seq_list[i],'carrier_id':carrier['carrier_id'][0]})

        datas={}
        datas['model'] = context.get('active_model', False) or 'stock.picking'
        datas['ids'] = context.get('active_ids', [])
        datas['report_name'] = report_name['report_name']
        # print report_name['paperformat_id'] and report_name['paperformat_id'][0]
        return {
            'type':'ir.actions.report.xml',
            'report_type':'qweb-pdf',
            'report_name':report_name['report_name'],
            'context':context,
        }
