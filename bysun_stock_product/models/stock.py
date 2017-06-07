# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class stock_move(models.Model):
    _inherit = 'stock.move'

    def action_done(self, cr, uid, ids, context=None):
        res = super(stock_move, self).action_done(cr, uid, ids, context)
        for move in self.browse(cr, uid, ids, context):
            self.pool.get('ebiz.stock').stock_move_changed(cr, uid, move, move.product_qty, context=context)
        return res

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    # 库存全量同步
    def auto_sync_qty(self, cr, uid, context=None):
        if context is None:
            context = {}
        product_model = self.pool['product.product']
        ebiz_stock_model = self.pool['ebiz.stock']
        location_model = self.pool['stock.location']
        sale_model = self.pool['sale.order.line']
        sync_location = location_model.search(cr, uid, [('is_sync','=',True)])
        context.update({'location':sync_location})
        draft_product_id = []
        cr.execute("select product_id from sale_order_line where state = 'draft' group by product_id")
        draft_product = cr.fetchall()
        if draft_product:
            draft_product_id = [x[0] for x in draft_product]
        all_product_ids = product_model.search(cr, uid, [('id','not in',draft_product_id),('active','=',True),('type','=','product'),('guid','not in',('',False))])
        ebiz_stock_ids = product_model.action_sync_qty(cr, uid, all_product_ids, context=context)
        ebiz_stock_model.sync_stock_qty(cr, uid, ebiz_stock_ids, context=context)
        return True

class stock_location(models.Model):
    _inherit = 'stock.location'

    is_sync = fields.Boolean(u'是否同步库存', default=True)
