# -*- coding: utf-8 -*- #

import time
from openerp import models, fields
import logging

_logger = logging.getLogger(__name__)


class ebiz_stock_sync_wizard(models.TransientModel):
    _name = 'ebiz.stock.sync.wizard'

    # sync_type = fields.Selection([('var', u'增量同步'), ('all', u'全量同步'), u'同步类型'])

    def ebiz_stock_sync_wizard(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids', [])
        stock_obj = self.pool.get('ebiz.stock')

        stocks = stock_obj.read(cr, uid, active_ids, ['var_qty', 'stock_qty', 'sync_check'], context=context)
        var_ids = [s['id'] for s in stocks if s['var_qty'] and s['sync_check']]
        # stock_ids = [s['id'] for s in stocks if s['stock_qty'] and s['sync_check']]

        stock_obj.sync_stock_var(cr, uid, var_ids)
        # stock_obj.sync_stock_qty(cr, uid, stock_ids)

        return {'type': 'ir.actions.act_window_close'}
