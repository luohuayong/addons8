# -*- coding: utf-8 -*-
import time
import openerp
from openerp import pooler
import logging
import datetime
from openerp.osv import fields,osv

_logger = logging.getLogger(__name__)
class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    def _get_date(dtype):
        """Return a function to compute the limit date for this type"""
        _logger.info("_________________")
        def calc_date(self, cr, uid, context=None):
            """Compute the limit date for a given date"""
            _logger.info(dtype)
            # logging.info(context)
            # logging.info(context.get('product_id', False))
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
                    duration_time = getattr(product, "life_time")
                    if dtype == "life_time":
                        duration = duration_time
                    elif dtype == "use_time":
                        duration = 0
                    elif dtype == "removal_time":
                        duration = duration_time * 3.0/4
                    elif dtype == "alert_time":
                        duration = duration_time * 2.0/3
                    _logger.info(duration_time)
                    _logger.info(duration)
                    # set date to False when no expiry time specified on the product
                    date = duration and (production_date
                        + datetime.timedelta(days=duration))
                    _logger.info(date)
            return date and date.strftime('%Y-%m-%d %H:%M:%S') or False
        return calc_date

    _defaults = {
        'name':'/',
        'life_date': _get_date('life_time'),
        'use_date': _get_date('use_time'),
        'removal_date': _get_date('removal_time'),
        'alert_date': _get_date('alert_time'),
    }