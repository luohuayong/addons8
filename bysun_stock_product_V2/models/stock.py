# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'self_support': fields.selection([('self_support_warehouse', u'自营仓'), ('virtual_warehouse', u'虚拟仓位')], u'仓库类型', required=True, default='virtual_warehouse'),
    	'x_delivery': fields.char(u'发货地'),
    }

