# -*- encoding: utf-8 -*-
import time
import openerp
from openerp import pooler
import logging
import datetime
from openerp.osv import fields,osv

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    _columns = {
        'production_date':fields.date(u'生产日期'),
    }

    def _check_lots_name(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        same = self.search(cr, uid, [('name','=',obj.name),('id','!=',obj.id)])
        if same:
            return False
        return True

    _constraints = [
        (_check_lots_name, u'批次号名字必须唯一，请重新正确的批次号', ['name']),
    ]

    def _get_date(dtype):
        """Return a function to compute the limit date for this type"""
        def calc_date(self, cr, uid, context=None):
            """Compute the limit date for a given date"""
            if context is None:
                context = {}
            if not context.get('product_id', False):
                date = False
            else:
                if not context.get('production_date',False):
                    date = False
                else:
                    production_date = context.get('production_date',False)
                    production_date = datetime.datetime.strptime(production_date,"%Y-%m-%d")
                    product = openerp.registry(cr.dbname)['product.product'].browse(
                        cr, uid, context['product_id'])
                    duration = getattr(product, dtype)
                    # set date to False when no expiry time specified on the product
                    date = duration and (production_date
                        + datetime.timedelta(days=duration))
            return date and date.strftime('%Y-%m-%d %H:%M:%S') or False
        return calc_date

    # Assign dates according to products data
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/') == '/':
            if vals.get('production_date',''):
                idx=self.search(cr,uid,[('name', 'like', vals['production_date'].replace('-',''))])
                serial = '%s%03d' % (vals['production_date'], len(idx)+1 )
                vals['name'] = serial.replace('-', '')
            else:
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, "stock.lot.serial")
        newid = super(stock_production_lot, self).create(cr, uid, vals, context=context)
        obj = self.browse(cr, uid, newid, context=context)
        towrite = []
        for f in ('life_date', 'use_date', 'removal_date', 'alert_date'):
            if not getattr(obj, f):
                towrite.append(f)
        context = dict(context or {})
        context['product_id'] = obj.product_id.id
        context['production_date'] = obj.production_date or False
        self.write(cr, uid, [obj.id], self.default_get(cr, uid, towrite, context=context))
        return newid

    _defaults = {
        'name':'/',
        'life_date': _get_date('life_time'),
        'use_date': _get_date('use_time'),
        'removal_date': _get_date('removal_time'),
        'alert_date': _get_date('alert_time'),
    }
