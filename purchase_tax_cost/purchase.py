# -*- coding: utf-8 -*- #
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
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
               val += line.product_qty * line.price_unit
            res[order.id]['amount_total'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_tax']=res[order.id]['amount_total'] - res[order.id]['amount_untaxed']

        return res
        
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The total amount"),
    }

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, group_id, context=context)
        unit_price_extax = order_line.price_unit
        if order_line.taxes_id and res:
            price_unit = order_line.price_unit
            unit_price_extax = self.pool.get('account.tax').compute_all(cr, uid, order_line.taxes_id, price_unit, 1, order_line.product_id, order.partner_id)['total']
            for move in res:
                move['price_unit'] = unit_price_extax
        return res
