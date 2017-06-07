# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp import models, fields as new_fields, api
from openerp import exceptions
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
import logging
import random

_logger = logging.getLogger(__name__)


class product_product(osv.osv):
    _inherit = 'product.product'

    def _compute_duration_qty(self, cr, uid, ids, context=None):
        _logger.info('in _compute_duration_qty')
        res = {}
        if not context.get('check_duration_qty', False):
            return res

        date_from = context.get('from_date')
        date_to = context.get('to_date')
        _logger.info('from: %s, to: %s' % (date_from, date_to))

        if not (date_from or date_to):
            raise exceptions.ValidationError(u'请先定义期初和期末的时间')

        prod_obj = self.pool.get('product.product')

        domain_products = [('product_id', 'in', ids)]
        domain_quant_closing, domain_move_in, domain_move_out = [], [], []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = prod_obj._get_domain_locations(cr, uid, ids, context=context)
        domain_move_in += prod_obj._get_domain_dates(cr, uid, ids, context=context) + [('state', '=', 'done')] + domain_products
        domain_move_out += prod_obj._get_domain_dates(cr, uid, ids, context=context) + [('state', '=', 'done')] + domain_products
        domain_quant_closing += domain_products

        domain_move_in += domain_move_in_loc
        domain_move_out += domain_move_out_loc
        moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty', 'valuation'], ['product_id'], context=context)
        moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty', 'valuation'], ['product_id'], context=context)

        domain_quant_closing += [('in_date', '<=', date_to)] + domain_quant_loc
        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant_closing, ['product_id', 'qty', 'inventory_value'], ['product_id'], context=context)
        quants = dict(map(lambda x: (x['product_id'][0], (x['qty'], x['inventory_value'])), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], (x['product_qty'], x['valuation'])), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], (x['product_qty'], x['valuation'])), moves_out))

        for product in self.browse(cr, uid, ids, context=context):
            pid = product.id
            closing_qty = float_round(quants.get(pid, (0.0, 0.0))[0], precision_rounding=product.uom_id.rounding)
            duration_incoming_qty = float_round(moves_in.get(pid, (0.0, 0.0))[0], precision_rounding=product.uom_id.rounding)
            duration_outgoing_qty = float_round(moves_out.get(pid, (0.0, 0.0))[0], precision_rounding=product.uom_id.rounding)
            opening_qty = float_round(quants.get(pid, (0.0, 0.0))[0] - moves_in.get(pid, (0.0, 0.0))[0] + moves_out.get(pid, (0.0, 0.0))[0], precision_rounding=product.uom_id.rounding)

            closing_stock_cost = float_round(quants.get(pid, (0.0, 0.0))[1], precision_rounding=0.01)
            duration_incoming_cost = float_round(moves_in.get(pid, (0.0, 0.0))[1], precision_rounding=0.01)
            duration_outgoing_cost = float_round(moves_out.get(pid, (0.0, 0.0))[1], precision_rounding=0.01)
            opening_stock_cost = float_round(closing_stock_cost - duration_incoming_cost + duration_outgoing_cost, precision_rounding=0.01)

            res[pid] = {
                'opening_qty': opening_qty,
                'closing_qty': closing_qty,
                'duration_outgoing_qty': duration_outgoing_qty,
                'duration_incoming_qty': duration_incoming_qty,
                'opening_stock_cost': opening_stock_cost,
                'closing_stock_cost': closing_stock_cost,
                'duration_incoming_cost': duration_incoming_cost,
                'duration_outgoing_cost': duration_outgoing_cost,
                'duration_from': date_from,
                'duration_to': date_to,
            }

        return res

    _columns = {
        'opening_qty': fields.float(string=u'期初库存'),
        'opening_stock_cost': fields.float(string=u'期初金额'),
        'closing_qty': fields.float(string=u'期末库存'),
        'closing_stock_cost': fields.float(string=u'期末金额'),
        'duration_incoming_qty': fields.float(string=u'期间入库'),
        'duration_incoming_cost': fields.float(string=u'入库金额'),
        'duration_outgoing_qty': fields.float(string=u'期间出库'),
        'duration_outgoing_cost': fields.float(string=u'出库金额'),
        'duration_from': fields.date(u'期间开始日期'),
        'duration_to': fields.date(u'期间结束日期'),
    }

    def recompute_duration_qty(self, cr, uid, ids, context=None):
        res = self._compute_duration_qty(cr, uid, ids, context=context)
        for pid, vals in res.iteritems():
            self.write(cr, uid, [pid], vals, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = dict(context or {})
        ids = super(product_product, self).search(cr, uid, args, offset, limit, order, context, count)
        # _logger.info('search returns :%s' % ids)
        if self._need_check_duration(cr, uid, ids, context=context):
            self.recompute_duration_qty(cr, uid, ids, context=context)
        return ids

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        ids = self.search(cr, uid, domain, context=context)
        if self._need_check_duration(cr, uid, ids, context=context):
            self.recompute_duration_qty(cr, uid, ids, context=context)
        return super(product_product, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)

    def _need_check_duration(self, cr, uid, ids, context=None):
        """判断是否需要计算duration的数据"""
        context = context or {}
        if not context.get('check_duration_qty', False):
            return False

        # date_from = context.get('from_date')
        # date_to = context.get('to_date')
        # _logger.info('check duration, from date: %s, to date: %s' % (date_from, date_to))

        # # 随机取出一条数据, 判断是否需要更新
        # p = self.browse(cr, uid, random.choice(ids), context=context)
        # if p.duration_from == date_from and p.duration_to == date_to:
        #     return False

        return True


class stock_move(models.Model):
    _inherit = 'stock.move'

    valuation = new_fields.Float(u'库存估值', compute='_compute_valuation', store=True, digits=(16, 2), help=u"库存移动的估值")

    @api.multi
    @api.depends('product_qty', 'price_unit')
    def _compute_valuation(self):
        for m in self:
            m.valuation = m.product_qty * m.price_unit
