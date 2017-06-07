# -*- coding: utf-8 -*- #

import time
from openerp import tools, api, exceptions
from openerp import models, fields
import logging
try:
    import xlwt
except ImportError:
    xlwt = None
import base64
from cStringIO import StringIO
_logger = logging.getLogger(__name__)

class stock_move_total(models.TransientModel):
    _name = 'stock.move.total'
    startdate=fields.Datetime(u'开始日期',required=True)
    enddate=fields.Datetime(u'结束日期',required=True)
    def from_data(self, cr, uid, ids, context=None):
        if context:
            data=self._get_data(cr, uid, ids, context=None)

            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white; borders: top thin, bottom thin, left thin, right thin;" )
            # try:
            if (worksheet):
                worksheet.write(0, 0, u'物品编码', content_title)
                worksheet.write(0, 1, u'物品名称', content_title)
                worksheet.write(0, 2, u'单位', content_title)
                worksheet.write(0, 3, u'单价（元）', content_title)
                worksheet.write(0, 4, u'进库数量', content_title)
                worksheet.write(0, 5, u'进库金额', content_title)
                worksheet.write(0, 6, u'销售出库数量', content_title)
                worksheet.write(0, 7, u'销售出库金额', content_title)
                worksheet.write(0, 8, u'销售退货数量', content_title)
                worksheet.write(0, 9, u'销售退货金额', content_title)
                worksheet.write(0, 10, u'盘点数量', content_title)
                worksheet.write(0, 11, u'借料消耗数量', content_title)
                worksheet.write(0, 12, u'借料消耗金额', content_title)
                worksheet.write(0, 13, u'借料赠送数量', content_title)
                worksheet.write(0, 14, u'借料赠送金额', content_title)
                worksheet.write(0, 15, u'借料销售数量', content_title)
                worksheet.write(0, 16, u'借料销售金额', content_title)
                worksheet.write(0, 17, u'报损数量', content_title)
                worksheet.write(0, 18, u'报损金额', content_title)
                worksheet.write(0, 19, u'期末数量', content_title)
                worksheet.write(0, 20, u'期末金额', content_title)
                worksheet.write(0, 21, u'供应商名称', content_title)
                worksheet.write(0, 22, u'供应商类别', content_title)
                worksheet.write(0, 23, u'是否有效', content_title)

                index = 0
                startRow = 1
                for line in data:
                    if line:
                        worksheet.write(startRow + index, 0, line[0], content_title)
                        worksheet.write(startRow + index, 1, line[1], content_title)
                        worksheet.write(startRow + index, 2, line[2], content_title)
                        worksheet.write(startRow + index, 3, line[3], content_title)
                        worksheet.write(startRow + index, 4, line[4], content_title)
                        worksheet.write(startRow + index, 5, line[5], content_title)
                        worksheet.write(startRow + index, 6, line[6], content_title)
                        worksheet.write(startRow + index, 7, line[7], content_title)
                        worksheet.write(startRow + index, 8, line[8], content_title)
                        worksheet.write(startRow + index, 9, line[9], content_title)
                        worksheet.write(startRow + index, 10, line[10], content_title)
                        worksheet.write(startRow + index, 11, line[11], content_title)
                        worksheet.write(startRow + index, 12, line[12], content_title)
                        worksheet.write(startRow + index, 13, line[13], content_title)
                        worksheet.write(startRow + index, 14, line[14], content_title)
                        worksheet.write(startRow + index, 15, line[15], content_title)
                        worksheet.write(startRow + index, 16, line[16], content_title)
                        worksheet.write(startRow + index, 17, line[17], content_title)
                        worksheet.write(startRow + index, 18, line[18], content_title)
                        worksheet.write(startRow + index, 19, line[19], content_title)
                        worksheet.write(startRow + index, 20, line[20], content_title)
                        worksheet.write(startRow + index, 21, line[21], content_title)
                        worksheet.write(startRow + index, 22, line[22], content_title)
                        worksheet.write(startRow + index, 23, line[23], content_title)

                    index += 1
            # except Exception, ex:
            #     _logger.info(Exception, ":", ex)
            fp = StringIO()
            workbook.save( fp )
            fp.seek( 0 )
            excel = fp.read()
            fp.close()
            return excel

    #导出订单收入
    def button_export(self, cr, uid, ids, context=None):
        excel = base64.encodestring( self.from_data(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'财务核算报表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':'sale_order.xls',
                 }
        try:
            attach_obj = self.pool.get('ir.attachment')
            doc_id = attach_obj.create(cr, uid, attach_vals)
        except Exception,ex:
            print Exception,":",ex

        return {
            'type' : 'ir.actions.act_url',
            'url':   '/web/binary/saveas?model=ir.attachment&field=datas&filename_field=name&id=%s' % ( doc_id ),
            'target': 'self',
            }

#so.total_fee as 订单总金额,
    def _get_data(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)

        startdate=sit.startdate
        enddate=sit.enddate

        _logger.info(startdate)
        _logger.info(enddate)

        query="""select pt.t_guid as 物品编码,pp.name_template as 物品名称,case pu.name  when 'Unit(s)' then '件' else pu.name end as 单位, sfee as 单价,
case when rp.supplier_mode in ('Consign','Commission') then coalesce(ccount,0)+coalesce(dcount,0)
else coalesce(acount,0)-coalesce(bcount,0)-coalesce(ocount,0)-coalesce(pcount,0) end as 进库数量,
case when rp.supplier_mode in ('Consign','Commission') then coalesce(cfee,0)+coalesce(dfee,0)
else coalesce(afee,0)-coalesce(bfee,0)-coalesce(ofee,0) end as 进库金额,coalesce(ccount,0)+coalesce(dcount,0) as 销售出库数量,coalesce(cfee,0)+coalesce(dfee,0) as 销售出库金额,
coalesce(ecount,0)+coalesce(fcount,0) as 销售退货数量,coalesce(efee,0)+coalesce(ffee,0) as 销售退货金额,coalesce(gcount,0)+coalesce(hcount,0) as 盘点数量,
coalesce(icount,0)+coalesce(jcount,0) as 借料消耗数量,coalesce(ifee,0)+coalesce(jfee,0) as 借料消耗金额,coalesce(kcount,0)+coalesce(lcount,0) as 借料赠送数量,coalesce(kfee,0)+coalesce(lfee,0) as 借料赠送金额,
coalesce(mcount,0)+coalesce(ncount,0) as 借料销售数量,coalesce(mfee,0)+coalesce(nfee,0) as 借料销售金额,qcount as 报损数量,qfee as 报损金额,coalesce(rcount,0)+coalesce(tcount,0) as 期末数量,coalesce(rfee,0)+coalesce(tfee,0) as 期末金额,rp.name as 供应商名称,
case rp.supplier_mode when 'Direct_Procurement' then '直采'
when 'Consign_stock_in' then '代售入仓'
when 'Commission' then '佣金'
when 'Consign' then '代售不入仓' end  as 供应商类别,pt.active as 商品有效
from
(select pp.id as product_id,a.count as acount,a.totalfee as afee,b.count as bcount,b.totalfee as bfee,
 c.count as ccount,c.totalfee as cfee,d.count as dcount,d.count*s.avfee as dfee
,e.count as ecount,e.totalfee as efee,f.count as fcount,f.count*s.avfee as ffee
,g.count as gcount,h.count as hcount
,i.count as icount,i.totalfee as ifee,j.count as jcount,j.count*s.avfee as jfee
,k.count as kcount,k.totalfee as kfee,l.count as lcount,l.count*s.avfee as lfee,
m.count as mcount,m.totalfee as mfee,n.count as ncount,n.count*s.avfee as nfee,o.count as ocount,o.totalfee as ofee,p.count as pcount,p.count*s.avfee as pfee,
q.count as qcount,q.totalfee as qfee,r.count as rcount,r.totalfee as rfee,s.avfee as sfee,t.count as tcount,t.count*s.avfee as tfee
from product_template pt
left join product_product pp on pp.product_tmpl_id=pt.id
left join
(
--采购入库
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,smin.product_id
from stock_move smin
left join stock_picking_type sptin on sptin.id = smin.picking_type_id
left join stock_quant_move_rel sqmr on sqmr.move_id = smin.id
left join stock_quant sq on sq.id = sqmr.quant_id
left join stock_picking sp on sp.id=smin.picking_id
where smin.state='done' and sptin.code='incoming'
and smin.date  between %s and %s and smin.location_id=8 and smin.location_dest_id=12
group by smin.product_id
order by smin.product_id
)a on pp.id=a.product_id
left join
(
select a.count-coalesce(b.count,0) as count,a.totalfee::NUMERIC-coalesce(b.totalfee,0)::NUMERIC as totalfee , a.product_id FROM
(
--采购退货(调拨)
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (251) and sm.location_id=12
group by  sm.product_id
order by  sm.product_id
) a
left join
(
--采购退货(反向调拨)
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (251) and sm.location_id=8
group by  sm.product_id
order by  sm.product_id
)b on a.product_id=b.product_id
)b on pp.id=b.product_id
left join
(
--销售出库(非组合商品)
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
inner join sale_order so on so.procurement_group_id = sp.group_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
left join product_product pp on sm.product_id=pp.id
left join product_template pt on pt.id=pp.product_tmpl_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and so.warehouse_id not in (118,119) and (pt.is_combination is null or pt.is_combination = 'f')
group by  sm.product_id
order by  sm.product_id
) c on pp.id=c.product_id
left join
(
--销售出库(组合商品原料)
SELECT SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
FROM stock_move sm
LEFT JOIN stock_picking_type spt ON spt. ID = sm.picking_type_id
LEFT JOIN stock_picking sp ON sp. ID = sm.picking_id
INNER JOIN sale_order so ON so.procurement_group_id = sp.group_id
LEFT JOIN stock_quant_move_rel sqmr ON sqmr.move_id = sm. ID
LEFT JOIN stock_quant sq ON sq. ID = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
WHERE sm. STATE = 'done'
AND spt.code = 'outgoing'
AND sm.date  between %s and %s
AND so.warehouse_id NOT IN (118, 119)
AND pt.is_combination = 't'
GROUP BY tempdt.slproduct_id
ORDER BY tempdt.slproduct_id
)d on pp.id=d.product_id
left join
(
--销售退货
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking sp on sp.id=sm.picking_id
left join stock_picking_type spt on spt.id = sp.picking_type_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done'
and sm.date  between %s and %s and (sp.picking_type_id =328 or spt.x_is_return = 't')
group by  sm.product_id
order by  sm.product_id
)e on pp.id=e.product_id
left join
(
--销售退货(组合商品原料)
select SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
where  sm.state='done'
and sm.date  between %s and %s and sp.picking_type_id =328
AND pt.is_combination = 't'
GROUP BY tempdt.slproduct_id
ORDER BY tempdt.slproduct_id
)f on pp.id=f.product_id
left join
(
--盘点数量
select sil.product_id,sum(sil.product_qty-sil.theoretical_qty) as count from stock_inventory si
left join stock_inventory_line sil on si.id=sil.inventory_id
left join product_product pp on sil.product_id=pp.id
left join product_supplierinfo ps on ps.product_tmpl_id=pp.product_tmpl_id
left join res_partner rp on ps.name=rp.id
where sil.product_qty<> sil.theoretical_qty and si.state='done' and rp.supplier_mode in ('Direct_Procurement','Consign_stock_in')
and si.create_date  between %s and %s
group by sil.product_id
)g on pp.id=g.product_id
left join
(
--盘点数量(组合商品原料)
select SUM ((sil.product_qty-sil.theoretical_qty)*tempdt.qty) as count,tempdt.slproduct_id as product_id
from stock_inventory si
left join stock_inventory_line sil on si.id=sil.inventory_id
left join product_product pp on sil.product_id=pp.id
left join product_supplierinfo ps on ps.product_tmpl_id=pp.product_tmpl_id
left join res_partner rp on ps.name=rp.id
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sil.prod_lot_id
where sil.product_qty<> sil.theoretical_qty and si.state='done' and rp.supplier_mode in ('Direct_Procurement','Consign_stock_in')
and si.create_date  between %s and %s AND pt.is_combination = 't'
group by tempdt.slproduct_id
)h on pp.id=h.product_id
left join
(
--活动借料消耗
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (369,375)
group by  sm.product_id
order by  sm.product_id
)i on pp.id=i.product_id
left join
(
--活动借料消耗(组合商品原料)
select SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (369,375) AND pt.is_combination = 't'
group by tempdt.slproduct_id
)j on pp.id=j.product_id

left join
(
--活动借料赠送
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (502,503)
group by  sm.product_id
order by  sm.product_id
)k on pp.id=k.product_id
left join
(
--活动借料赠送(组合商品原料)
select SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (502,503) AND pt.is_combination = 't'
group by tempdt.slproduct_id
)l on pp.id=l.product_id

left join
(
--活动借料销售
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (118,119)
group by  sm.product_id
order by  sm.product_id
)m on pp.id=m.product_id
left join
(
--活动借料销售(组合商品原料)
select SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (118,119) AND pt.is_combination = 't'
group by tempdt.slproduct_id
)n on pp.id=n.product_id

left join
(
--活动还料
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (118,119)
group by  sm.product_id
order by  sm.product_id
)o on pp.id=o.product_id
left join
(
--活动还料(组合商品原料)
select SUM (sq.qty*tempdt.qty) AS COUNT,SUM (sq.qty * sq. COST*tempdt.qty) AS totalfee,tempdt.slproduct_id as product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN product_product pp ON sm.product_id = pp. ID
LEFT JOIN product_template pt ON pt. ID = pp.product_tmpl_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
    WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id in (118,119) AND pt.is_combination = 't'
group by tempdt.slproduct_id
)p on pp.id=p.product_id
left join
(
--报损出库
select SUM(sq.qty) as count,SUM(sq.qty*sq.cost) as totalfee,sm.product_id
from stock_move sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where  sm.state='done' and spt.code='outgoing'
and sm.date  between %s and %s and sp.picking_type_id =252
group by  sm.product_id
order by  sm.product_id
)q on pp.id=q.product_id
left join
(
--期末库存
select coalesce(b.count,0)-coalesce(a.count,0) as count,round(coalesce(b.totalfee,0)::NUMERIC -coalesce(a.totalfee,0)::NUMERIC,2) as totalfee,coalesce(a.product_id,b.product_id) as product_id
from
(
select sum(sq.qty) as count,sum(sq.qty*sq.cost) as totalfee,sm.product_id from stock_move sm
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where sm.state='done'
and ((sm.location_id=12 and sm.location_dest_id=8)
or (sm.location_id=12 and sm.location_dest_id=5)
or (sm.location_id=12 and sm.location_dest_id=7)
or (sm.location_id=12 and sm.location_dest_id=4)
or (sm.location_id=15 and sm.location_dest_id=9)
or (sm.location_id=721 and sm.location_dest_id=9)
or (sm.location_id=715 and sm.location_dest_id=9))
and sm.create_date < %s
group by sm.product_id
) a full join
(
select sum(sq.qty) as count,sum(sq.qty*sq.cost) as totalfee,sm.product_id from stock_move  sm
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
where sm.state='done'
and ((sm.location_id=8 and sm.location_dest_id=12)
or (sm.location_id=9 and sm.location_dest_id=12)
or (sm.location_id=5 and sm.location_dest_id=12)
or (sm.location_id=7 and sm.location_dest_id=12))
and sm.create_date < %s
group by sm.product_id
) b on a.product_id =b.product_id
left join product_product pp on a.product_id=pp.id
left join product_template pt on pp.product_tmpl_id=pt.id
where (pt.is_combination is null or pt.is_combination = 'f')
)r on pp.id=r.product_id
left join
(
--期末库存(组合商品原料)
select coalesce(b.count,0)-coalesce(a.count,0) as count,round(coalesce(b.totalfee,0)::NUMERIC -coalesce(a.totalfee,0)::NUMERIC,2) as totalfee,coalesce(a.product_id,b.product_id) as product_id
from
(
select sum(sq.qty*tempdt.qty) as count,sum(sq.qty*sq.cost*tempdt.qty) as totalfee,tempdt.slproduct_id as product_id from stock_move sm
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
		WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
left join product_product pp on sm.product_id=pp.id
left join product_template pt on pp.product_tmpl_id=pt.id
where sm.state='done'
and ((sm.location_id=12 and sm.location_dest_id=8)
or (sm.location_id=12 and sm.location_dest_id=5)
or (sm.location_id=12 and sm.location_dest_id=7)
or (sm.location_id=12 and sm.location_dest_id=4)
or (sm.location_id=15 and sm.location_dest_id=9)
or (sm.location_id=721 and sm.location_dest_id=9)
or (sm.location_id=715 and sm.location_dest_id=9))
and sm.create_date < %s
and pt.is_combination = 't'
group by tempdt.slproduct_id
) a full join
(
select sum(sq.qty*tempdt.qty) as count,sum(sq.qty*sq.cost*tempdt.qty) as totalfee,tempdt.slproduct_id as product_id from stock_move  sm
left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
left join stock_quant sq on sq.id = sqmr.quant_id
LEFT JOIN (
    SELECT DISTINCT spl.product_id AS slproduct_id,sp.product_id AS sproduct_id,sp.stock_lot, spl.product_uom_qty/sp.product_uom_qty as qty
    FROM stock_production sp
    LEFT JOIN stock_production_line spl ON spl.product_order = sp. ID
		WHERE sp .processing_type = 'many2one'
    ORDER BY sp.product_id
) tempdt ON tempdt.stock_lot = sq.lot_id
left join product_product pp on sm.product_id=pp.id
left join product_template pt on pp.product_tmpl_id=pt.id
where sm.state='done'
and ((sm.location_id=8 and sm.location_dest_id=12)
or (sm.location_id=9 and sm.location_dest_id=12)
or (sm.location_id=5 and sm.location_dest_id=12)
or (sm.location_id=7 and sm.location_dest_id=12))
and sm.create_date < %s
and pt.is_combination = 't'
group by tempdt.slproduct_id
) b on a.product_id =b.product_id
)t on pp.id=t.product_id
left join
(
--加权平均单价
select SUM(sq.qty*sq.cost)/SUM(sq.qty) as avfee,smin.product_id
from stock_move smin
left join stock_picking_type sptin on sptin.id = smin.picking_type_id
left join stock_quant_move_rel sqmr on sqmr.move_id = smin.id
left join stock_quant sq on sq.id = sqmr.quant_id
left join stock_picking sp on sp.id=smin.picking_id
where smin.state='done' and sptin.code='incoming'
and smin.date < %s and smin.location_id=8 and smin.location_dest_id=12
group by smin.product_id
order by smin.product_id
)s on pp.id=s.product_id
 order by pp.id
)c
left join product_product pp on c.product_id=pp.id
left join product_supplierinfo ps on ps.product_tmpl_id=pp.product_tmpl_id
left join res_partner rp on ps.name=rp.id
left join product_template pt on pt.id=pp.product_tmpl_id
left join product_uom pu on pt.uom_id=pu.id
where pt.is_combination is null or pt.is_combination = 'f'
order by 供应商类别 desc ,t_guid

"""
        cr.execute(query,([startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,enddate,enddate,enddate,enddate,enddate]))
        data = cr.fetchall()
        _logger.info('----------_get_data------------')
        # _logger.info(data)
        _logger.info('----------_get_data------------')
        return data
