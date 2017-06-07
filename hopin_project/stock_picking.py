# -*- coding: utf-8 -*-

from openerp.osv import osv, fields, expression
import logging

_logger = logging.getLogger(__name__)
class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'partner_shipping_mobile':fields.related('sale_id','partner_shipping_mobile',type='char',relation='sale.order',string= u'收货人电话')
    }