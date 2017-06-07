# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import osv,fields
from openerp import api, models
from datetime import datetime
from openerp import tools

class customer_move(osv.osv):
    _name = 'customer.move'
    _description = "Customer Move Report Data"
    _auto = False

    _columns = {
        'id':fields.integer(u'序号'),
        'loc_rack':fields.char(u'货架号'),
        'sku':fields.char(u'产品编码'),
        'prod_name':fields.char(u'产品名称'),
        'temp_zone':fields.char(u'温区'),
        'loc_row':fields.char(u'行号'),
        'loc_case':fields.char(u'盒号'),
        'ean13':fields.char(u'国际码'),
        'wave_name':fields.char(u'波次号'),
        'order_name':fields.char(u'订单号'),
        'qty':fields.float(u'总数'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'customer_move')
        cr.execute("""create or replace view customer_move as
        	select row_number() over (order by pp.id, sp.id, spw.id) as id,
            sp.id as picking_id,
            pp.id as product_id,
            pp.guid as sku,
            pt.loc_rack as loc_rack,
            pt.temp_zone as temp_zone,
            pt.loc_row as loc_row,
            pt.loc_case as loc_case,
            pt.name as prod_name,
            pp.ean13 as ean13,
            spw.name as wave_name,
            sp.origin as order_name,
            sm.product_uom_qty as qty,
            sl.name as location_id
            from
            stock_move sm
            join
            stock_picking sp
            on sm.picking_id = sp.id
            left join
            stock_picking_wave spw
            on sp.wave_id = spw.id
            join
            product_product pp
            on pp.id = sm.product_id
            join
            product_template pt
            on pp.product_tmpl_id = pt.id
            join
            stock_location sl
            on sl.id = sm.location_id
            order by
            pp.id,
            sp.id,
            spw.id
        	""")