# -*- coding: utf-8 -*-

import time, xlrd,base64
from openerp.osv import osv, fields
import  logging

class import_excel(osv.osv_memory):
    _name = 'import.excel'

    _columns = {
        'excelfile':fields.binary(u'上传excel文件')
    }

    def on_file_load(self, cr, uid, ids, context=None):
        try:
            if context is None:
                context = {}
            excel_obj=self.browse(cr, uid, ids[0])
            excelfile = excel_obj.excelfile
            exceldate = xlrd.open_workbook(file_contents=base64.decodestring(excelfile))
            sh = exceldate.sheet_by_index(0)
            for rx in range(1,sh.nrows):
                orderno=sh.cell(rx, 0).value
                if orderno:
                    expresscompany=sh.cell(rx, 10).value
                    delivery_carrier_obj=self.pool['delivery.carrier']
                    carrier_ids=delivery_carrier_obj.search(cr,uid,[('name','=',expresscompany)],context=context)
                    expressnumber=sh.cell(rx, 11).value
                    stock_picking_obj=self.pool['stock.picking']
                    ids=stock_picking_obj.search(cr,uid,[('origin','=',orderno)],context=context)
                    stock_picking_obj.write(cr, uid, ids, {'carrier_id': carrier_ids[0],'carrier_tracking_ref':expressnumber}, context=context)
                else:
                    continue
        except Exception, e:
            raise osv.except_osv('Error !', u'更新快递信息失败，请检查excel表中的数据!')
        return True