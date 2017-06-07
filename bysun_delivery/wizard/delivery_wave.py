# -*- coding: utf-8 -*- #

import time
from openerp.osv import osv, fields
import logging

class oscg_upload_barcode(osv.osv_memory):
    _name = 'oscg.upload.barcode'

    _columns = {
        'upload_barcode':fields.text(u'条码'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        stock_picking = self.pool['stock.picking']
        wave_model = self.pool['stock.picking.wave']
        i = self.read(cr, uid, ids[0], ['upload_barcode'])
        if i['upload_barcode']:
            pack_model = self.pool['stock.quant.package']
            wave_id = context.get('active_id',False)
            wave = wave_model.browse(cr, uid, wave_id)
            error_order = ''
            a1 = i['upload_barcode'].replace(' ',',')
            a2 = a1.replace('\n',',')
            a = a2.split(',')
            for ab in a:
                if not ab: continue
                picking_ids = stock_picking.search_by_package(cr, uid, ab, context=context)
                if picking_ids:
                    stock_picking.write(cr, uid, picking_ids, {'wave_id': wave_id,'carrier_id':wave.carrier_id and wave.carrier_id.id or False}, context=context)
                else:
                    error_order += u"找不到运单[%s]\n" % ab
            if error_order:
                self.pool['stock.picking.wave'].write(cr, uid, wave_id, {'error_order':error_order})
        return True