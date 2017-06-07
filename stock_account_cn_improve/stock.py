# -*- encoding: utf-8 -*-

from openerp import api, fields, models, _

class stock_inventory(models.Model):
    _inherit = "stock.inventory"
    _description = u'盘点继承'

    product_type = fields.Selection([('Direct_Procurement',u'直采'),('Consign_stock_in',u'代售入仓')],u'产品类型')
    notes = fields.Text(u'盘点备注')

    def _get_inventory_lines(self, cr, uid, inventory, context=None):
        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        location_ids = location_obj.search(cr, uid, [('id', 'child_of', [inventory.location_id.id])], context=context)
        domain = ' location_id in %s'
        args = (tuple(location_ids),)
        if inventory.partner_id:
            domain += ' and owner_id = %s'
            args += (inventory.partner_id.id,)
        if inventory.lot_id:
            domain += ' and lot_id = %s'
            args += (inventory.lot_id.id,)
        if inventory.product_id:
            domain += ' and product_id = %s'
            args += (inventory.product_id.id,)
        if inventory.package_id:
            domain += ' and package_id = %s'
            args += (inventory.package_id.id,)
        if inventory.product_type:
            domain += ' and rp.supplier_mode = %s'
            args += (inventory.product_type,)

        cr.execute('''
           SELECT sq.product_id, sum(sq.qty) as product_qty, sq.location_id, sq.lot_id as prod_lot_id, sq.package_id, sq.owner_id as partner_id 
           FROM stock_quant as sq join product_product as pp on sq.product_id=pp.id 
           join product_template as pt on pp.product_tmpl_id=pt.id 
           join product_supplierinfo as pso on pso.product_tmpl_id=pt.id 
           join res_partner as rp on rp.id=pso.name 
           WHERE''' + domain + ''' 
           GROUP BY sq.product_id, sq.location_id, sq.lot_id, sq.package_id, sq.owner_id 
        ''', args)
        vals = []
        for product_line in cr.dictfetchall():
            #replace the None the dictionary by False, because falsy values are tested later on
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            product_line['inventory_id'] = inventory.id
            product_line['theoretical_qty'] = product_line['product_qty']
            if product_line['product_id']:
                product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                product_line['product_uom_id'] = product.uom_id.id
            vals.append(product_line)
        return vals

class stock_inventory_line(models.Model):
    _inherit = 'stock.inventory.line'
    _order = "loc_rack,product_name,prodlot_name"

    loc_rack = fields.Char(related="product_id.loc_rack", string=u'货架', store=True)

class stock_inventory_simple(models.TransientModel):
    _inherit = 'stock.inventory.simple'

    def action_upload(self, cr, uid, ids, context=None):
        inv = self.browse(cr, uid, ids[0])
        if inv.upload_code:
            product_obj = self.pool['product.product']
            inventory_obj = self.pool['stock.inventory']
            lot_obj = self.pool['stock.production.lot']
            error_code = ''
            inventory_lines = []
            inv_id = context.get('active_id',False)
            inventory_record = inventory_obj.read(cr, uid, inv_id, ['location_id','product_type'])
            location_id = inventory_record['location_id'][0]
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
                if product_id:
                    product_record = self.pool['product.product'].browse(cr, uid, product_id, context=context)
                    if inventory_record['product_type']:
                        if product_record.seller_id.supplier_mode != inventory_record['product_type']:
                            continue
                if not error_code:
                    # uom_id = self.pool['product.product'].read(cr, uid, product_id, ['uom_id',], context=context)['uom_id'][0]
                    product_record = self.pool['product.product'].browse(cr, uid, product_id, context=context)
                    inv_line = self.pool['stock.inventory.line'].onchange_createline(cr, uid, ids, location_id=location_id, product_id=product_id, uom_id = product_record.uom_id.id, prod_lot_id=lot_id, context=context)
                    res = {
                        'product_id': product_id,
                        'location_id': location_id,
                        'product_uom_id': product_record.uom_id.id,
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
