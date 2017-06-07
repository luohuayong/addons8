# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp import api, models
from datetime import datetime

class delivery_order_report(models.AbstractModel):
    _name = 'report.bysun_delivery.oscg_delivery_order'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        report = report_obj._get_report_from_name(cr, uid, 'bysun_delivery.oscg_delivery_order')
        if not data:return True
        # operation_model = self.pool['stock.pack.operation']
        # operation_ids = operation_model.search(cr, uid, [('picking_id','in',data)])
        # if not operation_ids:
        #     raise osv.except_osv(('错误!'),("没有包裹信息"))
        # picking = {}
        # for operation in operation_model.browse(cr, uid, operation_ids, context=context):
        #     if not picking.has_key(operation.picking_id):
        #         picking.update({operation.picking_id:[operation]})
        #     else:
        #         picking[operation.picking_id].append(operation)
        pickings = self.pool['stock.picking'].browse(cr, uid, data, context=context)
        now_time = datetime.now().strftime('%Y-%m-%d')
        docargs = {
            'docs':pickings,
            'now_time':now_time,
            'doc_ids': report.ids,
            'doc_model': report.model,
            }
        return report_obj.render(cr, uid, ids, 'bysun_delivery.oscg_delivery_order', docargs, context=context)

