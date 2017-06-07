# -*- coding: utf-8 -*- #
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class sale_order(osv.osv):
    _inherit = "sale.order"

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += line.price_unit * line.product_uom_qty
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_tax'] = res[order.id]['amount_total'] - res[order.id]['amount_untaxed']
        return res
