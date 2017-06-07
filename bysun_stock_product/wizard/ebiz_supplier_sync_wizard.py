# -*- coding: utf-8 -*- #

import time
from openerp import models, fields
import logging

_logger = logging.getLogger(__name__)


class ebiz_supplier_sync_wizard(models.TransientModel):
    _name = 'ebiz.supplier.sync.wizard'

    # sync_type = fields.Selection([('var', u'增量同步'), ('all', u'全量同步'), u'同步类型'])

    def ebiz_supplier_sync_wizard(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids', [])
        supplier_obj = self.pool.get('res.partner')

        supplier = supplier_obj.read(cr, uid, active_ids, ['supplier'], context=context)
        var_ids = [s['id'] for s in supplier if s['supplier']]
        # stock_ids = [s['id'] for s in stocks if s['stock_qty'] and s['sync_check']]

        supplier_obj.sync_supplier(cr, uid, var_ids)
        # stock_obj.sync_stock_qty(cr, uid, stock_ids)

        return {'type': 'ir.actions.act_window_close'}