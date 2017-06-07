# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ebiz_product_sync_wizard(models.TransientModel):
    _name = 'ebiz.product.sync.wizard'

    def ebiz_product_sync_wizard(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids', [])
        self.pool.get('product.template').sync_product(cr, uid, active_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}
