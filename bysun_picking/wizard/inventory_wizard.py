# -*- encoding: utf-8 -*-
from openerp import tools,api
from openerp.osv import fields,osv

class stock_inventory_simple(osv.osv_memory):

    _name = 'stock.inventory.simple'

    _columns = {
        'upload_code':fields.text(u'条码'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        inv = self.browse(cr, uid, ids[0])
        if inv.upload_code:
            product_obj = self.pool['product.product']
            inventory_obj = self.pool['stock.inventory']
            lot_obj = self.pool['stock.production.lot']
            error_code = ''
            inventory_lines = []
            inv_id = context.get('active_id',False)
            location_id = inventory_obj.read(cr, uid, inv_id, ['location_id'])['location_id'][0]
            upload_code = inv.upload_code.split('\n')
            for line in upload_code:
                l = line.split(',')
                if len(l) < 2:
                    error_code += u'格式错误：%s\n' % line
                    continue
                lot_ids = lot_obj.search(cr, uid, ['|', ('name', '=', l[0]), ('ref', '=', l[0])], context=context)
                product_id = False
                lot_id = False
                if lot_ids:
                    lot_id = lot_ids[0]
                    lots = lot_obj.read(cr, uid, lot_ids[0], ['product_id',], context=context)
                    product_id = lots['product_id'][0]
                else:
                    p_ids = product_obj.search(cr, uid, ['|', ('default_code', '=', l[0]), ('ean13', '=', l[0])], context=context)
                    if p_ids:
                        product_id = p_ids[0]
                    else: 
                        error_code += u'批次/产品不存在：%s\n' % line
                        continue
                if not error_code:
                    uom_id = self.pool['product.product'].read(cr, uid, product_id, ['uom_id',], context=context)['uom_id'][0]
                    inv_line = self.pool['stock.inventory.line'].onchange_createline(cr, uid, ids, location_id=location_id, product_id=product_id, uom_id = uom_id, prod_lot_id=lot_id, context=context)
                    res = {
                        'product_id': product_id,
                        'location_id': location_id,
                        'product_uom_id': uom_id,
                        'prod_lot_id': lot_id,
                        'theoretical_qty': inv_line['value']['theoretical_qty'],
                        'product_qty': float(l[1]),
                    }
                    is_in = False
                    for inventory_line in inventory_lines:
                        if inventory_line[2]['product_id'] == product_id and inventory_line[2]['prod_lot_id'] == lot_id:
                            inventory_line[2]['product_qty'] += float(l[1])
                            is_in = True
                    if not is_in:
                        inventory_lines.append((0,0, res))
            if not error_code:
                inventory_obj.write(cr, uid, inv_id, {'line_ids':inventory_lines})
            else:
                raise osv.except_osv(u'错误', u'条码数据错误：\n%s' % error_code)
        return True
