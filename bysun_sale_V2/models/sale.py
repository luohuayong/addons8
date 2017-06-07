# -*- coding: utf-8 -*-

from openerp.osv import fields, osv, expression
import logging
import json
import time,datetime
import base64

_logger = logging.getLogger(__name__)


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _get_sale_ids(self, cr, uid, ids, context=None):
    	if not isinstance(ids,list):
    		ids = [ids]
    	sale_model = self.pool['sale.order']
    	sale_ids = sale_model.search(cr, uid, [('partner_shipping_id','in',ids),('state','not in',('cancel','done')),('shipped','!=',True)])
    	return sale_ids

    _columns = {
        'discount_mode':fields.char(u'优惠模式'),
        'total_fee': fields.float(u'订单总费用'),
    	'partner_shipping_mobile':fields.related('partner_shipping_id','mobile',string=u'收货人电话',type='char',
    	store={
                'sale.order': (lambda self,c,u,ids,context:ids, ['partner_shipping_id'], 10),
                'res.partner':(_get_sale_ids, ['mobile'],10),
           	}),
        'is_selftake':fields.boolean(u'自提单'),
    }

    _defaults = {
        'is_selftake':False,
    }

    def _prepare_order(self, cr, uid, order, partner_id, delivery_addr_id, invoice_addr_id, context=None):
        vals = super(sale_order, self)._prepare_order(cr, uid, order, partner_id, delivery_addr_id, invoice_addr_id, context=context)

        vals.update({
            'total_fee': order['total_fee'],
            'discount_mode': order['discount_mode'],
        })
        return vals