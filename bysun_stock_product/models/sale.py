# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)

class sale_order_status_sync(models.Model):
    _name = 'sale.order.status.sync'

    order_id = fields.Many2one('sale.order', u'销售订单', required=True)
    order_state = fields.Selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], '销售单状态', readonly=True)
    state = fields.Selection([('wait',u'未同步'),('progress',u'同步中'),('done',u'已同步'),('fail',u'同步失败')], u'状态')
    sync_log = fields.Text(u'返回信息')

    _defaults = {
        'state':'wait',
    }

    def action_sync_orderstatus(self, cr, uid, ids, context=None):
        vals = {'orderstate_info':[]}
        shop_model = self.pool['ebiz.shop']
        state_dict = {'progress':'audited','cancel':'cancelled'}
        wait_sync_list = []
        for state_read in self.read(cr, uid, ids, ['state'],context=context):
            if state_read['state'] not in ('wait','fail'):continue
            wait_sync_list.append(state_read['id'])
        _logger.info('1111111111111111111111%s'%wait_sync_list)
        if wait_sync_list:
            self.write(cr, uid, wait_sync_list, {'state':'progress'})
            for wait_sync in self.browse(cr, uid, wait_sync_list):
                vals['orderstate_info'].append({
                    'order_no':wait_sync.order_id.name,
                    'order_status':state_dict.get(wait_sync.order_state,''),
                    'update_date':wait_sync.create_date,
                    })
            print vals
            res = shop_model.remote_call(cr, uid, 'order', 'orderstatesync', **vals)
            _logger.info(res)
            # 加返回信息判断
            self.write(cr, uid, wait_sync_list, {'state':'done', 'sync_log':res})
        return True

class sale_order(models.Model):
    _inherit = 'sale.order'

    logistic_line = fields.One2many('sale.order.logistic', 'order_id', u'物流信息', readonly = True, copy=False)
    is_cod = fields.Boolean(u'货到付款')

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        sync_ids = []
        sale_state_sync_model = self.pool['sale.order.status.sync']
        for id in ids:
            sync_id = sale_state_sync_model.create(cr, uid, {
                'order_state':'progress',
                'order_id':id,
                'state':'wait',
                })
            sync_ids.append(sync_id)
        _logger.info('2222222222222222222222%s'%sync_ids)
        sale_state_sync_model.action_sync_orderstatus(cr, uid, sync_ids, context=context)
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_cancel(cr, uid, ids, context=context)
        sync_ids = []
        sale_state_sync_model = self.pool['sale.order.status.sync']
        for id in ids:
            sync_id = sale_state_sync_model.create(cr, uid, {
                'order_state':'cancel',
                'order_id':id,
                'state':'wait',
                })
            sync_ids.append(sync_id)
        _logger.info('333333333333333333333333%s'%sync_ids)
        sale_state_sync_model.action_sync_orderstatus(cr, uid, sync_ids, context=context)
        return res

class sale_order_logistic(models.Model):
    _name = 'sale.order.logistic'
    _description = u'订单物流信息'

    name = fields.Selection([ ('print', u'打单'), ('package', u'打包'), ('send', u'出库'), ('signed', u'签收'),], u'物流操作', required=True, readonly = True)
    create_date = fields.Datetime(u'时间', readonly = True)
    user_id = fields.Many2one('res.users', string=u"操作员", required=True, readonly = True)
    memo = fields.Char(u'备注', )
    order_id = fields.Many2one('sale.order', string=u"订单", required=True, readonly = True)
    carrier_id = fields.Many2one('delivery.carrier',u'物流方法')
    carrier_no = fields.Char(u'物流单号')
    state = fields.Selection([ ('no', u'不同步'), ('draft', u'待同步'), ('send', u'已同步'), ('error', u'同步错误'),], u'同步状态', required=True, readonly = True)
    
    _defaults = {
        'state': 'draft',
    }

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'send'}, context = context)
        return True

    def create(self, cr, uid, vals, context=None):
        res = super(sale_order_logistic, self).create(cr, uid, vals, context=context)
        self.action_sync_logistic(cr, uid, [res], context=context)
        return res

    def action_sync_logistic(self, cr, uid, ids, context=None):
        sale_model = self.pool['sale.order']
        eibz_shop_model = self.pool['ebiz.shop']
        logistic_dict = {'print':1, 'package':2, 'send':3}
        for logistic in self.browse(cr, uid, ids, context=context):
            if logistic.state not in ('draft','error'):continue
            post_data = {
                'order_no':logistic.order_id.name,
                'status':logistic_dict.get(logistic.name,False),
                'memo':logistic.memo,
                'user':logistic.user_id and logistic.user_id.name or '',
                'create_date':logistic.create_date,
                'express_info':[{
                    'express_company':logistic.carrier_id and logistic.carrier_id.name or '',
                    'express_no':logistic.carrier_no or '',
                    }],
            }
            res = eibz_shop_model.remote_call(cr, uid, 'order','logisticsync', **post_data)
            _logger.info(res)
            if 'success' == res.get('result', 'fail'):
                logistic.write({'state':'send'})
            else:
                logistic.write({'state':'error'})
        return True