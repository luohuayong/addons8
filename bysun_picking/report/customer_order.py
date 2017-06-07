# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<https://www.zhiyunerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import osv
from openerp import api, models
from datetime import datetime,timedelta


class delivery_customer_order(models.AbstractModel):
    _name = 'report.bysun_picking.oscg_customer_order'

    def render_html(self, cr, uid, ids, data=None, context=None):
        if data is None:
            data = {}
        stock_picking = self.pool['stock.picking']
        sale_order = self.pool['sale.order']
        group_obj = self.pool['procurement.group']
        if not data.get('ids',False):return True
        picking_ids = data.get('ids',False)
        if not isinstance(picking_ids,list): picking_ids = [picking_ids]
        report_obj = self.pool['report']
        report = report_obj._get_report_from_name(cr, uid, 'bysun_picking.oscg_customer_order')
        if not isinstance(ids,list): ids = [ids]
        res = []
        picking_name = {}
        for picking in stock_picking.read(cr, uid, picking_ids, ['id', 'origin', 'name', 'sale_id'], context):
            # so_ids = stock_picking.get_sale_order(cr, uid, picking['id'], context)
            if not picking['sale_id']:
                #raise osv.except_osv(('警告!'),("单号%s没有对应的销售订单，不能打印客户单" % picking['name']))
                pass
            else:
                res.append(sale_order.browse(cr, uid, picking['sale_id'][0],context=context))
                # picking_name[picking['sale_id'][0]] = '/report/barcode/?type=%s&width=%s&height=%s&value=%s&humanreadable=1' % ('Code128', 600, 150, picking['name'])
                picking_name[picking['sale_id'][0]] = picking['name']
        docargs = {
            'docs': res,
            'picking_name': picking_name,
            'doc_ids': report.ids, 
            'doc_model': report.model, 
        }
        return report_obj.render(cr, uid, ids, 'bysun_picking.oscg_customer_order', docargs, context=context)

class oscg_zongjiandan(models.AbstractModel):
    _name = 'report.bysun_picking.zongjiandan'

    def get_data(self, cr, uid, ids, context=None):
        res = {}
        sql = """
SELECT concat(loc_rack,'-',loc_row,'-',loc_case) as pos, product_id, sku, ean13, prod_name, lot, sum(qty) as qty, 
       row_number() over (order by loc_rack, loc_row, loc_case, product_id) as pp_id from (
  SELECT sq.product_id as product_id, pp.default_code as sku, pp.ean13 as ean13, pp.name_template as prod_name, 
         pt.loc_rack as loc_rack, pt.loc_row as loc_row, pt.loc_case as loc_case, pt.temp_zone as temp_zone, sq.reservation_id as reservation_id, 
         sq.lot_id as lot_id, sq.qty as qty, sm.product_qty as sm_qty, sm.product_uom as uom, sm.picking_id as picking_id, spt.name as lot       
  FROM stock_quant sq
  join stock_move sm on (sq.reservation_id = sm.id)  
  left join product_product pp on (sq.product_id = pp.id) 
  join product_template pt on (pp.product_tmpl_id = pt.id) 
  left join stock_production_lot spt on (spt.id = sq.lot_id) 
  where sm.picking_id in %s) qm 
group by product_id, sku, ean13, prod_name, loc_rack, loc_row, loc_case, lot 
"""
        cr.execute(sql, (tuple(ids),) )
        res['Picking'] = cr.dictfetchall()
        # cr.execute(sql, (tuple(ids), 'C') )
        # res['C'] = cr.dictfetchall()
        # cr.execute(sql, (tuple(ids), 'F') )
        # res['F'] = cr.dictfetchall()
        return res

    def render_html(self, cr, uid, ids, data=None, context=None):
        if data is None:
            data = {}
        user_name = self.pool['res.users'].read(cr, uid, uid, ['name'])['name']
        now_time = (datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        report_obj = self.pool['report']
        report = report_obj._get_report_from_name(cr, uid, 'bysun_picking.zongjiandan')
        if not data.get('ids',False):return True
        picking_ids = data.get('ids',False)
        if not isinstance(ids,list): ids = [ids]
        if not isinstance(picking_ids,list): picking_ids = [picking_ids]
        res = self.get_data(cr, uid, picking_ids, context=context)
        docargs = {
            'docs': res,
            'doc_ids': report.ids, 
            'doc_model': report.model,
            'user_name':user_name,
            'now_time':now_time,
        }
        return report_obj.render(cr, uid, ids, 'bysun_picking.zongjiandan', docargs, context=context)

