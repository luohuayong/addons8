# -*- coding: utf-8 -*- #

import time
from openerp.osv import osv, fields
import logging

logger = logging.getLogger(__name__)
class delivery_order_print(osv.osv_memory):
    _name = 'delivery.order.print'

    def print_zongjian(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas={}
        datas['model'] = context.get('active_model', False) or 'stock.picking'
        datas['ids'] = context.get('active_ids', [])

        # 挂起状态检查
        sale_model = self.pool['sale.order']
        sale_logistic = self.pool['sale.order.logistic']
        for picking in self.pool[datas['model']].read(cr, uid, datas['ids'], ['pending','name','group_id','state']):
            if picking['pending']: raise osv.except_osv(u'警告 !', u'发货单%s已经挂起,不能进行备货!' % picking['name'])
            if picking['state'] == 'cancel':continue
            sale_id = sale_model.search(cr, uid, [('name', '=', picking['group_id'] and picking['group_id'][1])])
            if sale_id:
                sale_logistic.create(cr, uid, {
                    'name':'print',
                    'user_id':uid,
                    'order_id':sale_id[0],
                    'state':'draft',
                    'memo':u'打单拣货中',
                    })
        return {
            'type':'ir.actions.report.xml',
            'report_type':'qweb-pdf',
            'report_name':'bysun_picking.zongjiandan',
            'data': datas,
        }

    def close_clear(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def print_kehudan(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas={}
        datas['model'] = context.get('active_model', False) or 'stock.picking'
        datas['ids'] = context.get('active_ids', [])

        # 挂起状态检查
        sale_model = self.pool['sale.order']
        for picking in self.pool[datas['model']].read(cr, uid, datas['ids'], ['pending','name']):
            if picking['pending']: raise osv.except_osv(u'警告 !', u'发货单%s已经挂起,不能进行备货!' % picking['name'])
        return {
            'type':'ir.actions.report.xml',
            'report_name':'bysun_picking.oscg_customer_order',
            'report_type':'qweb-pdf',
            'data':datas,
        }

