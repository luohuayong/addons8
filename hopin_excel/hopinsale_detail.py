# -*- coding: utf-8 -*-

import time,datetime
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

class HopinSaleDetail(models.TransientModel):
    _name = 'hopinsale_detail'
    startdate=fields.Datetime(u'开始日期',required=True)
    enddate=fields.Datetime(u'结束日期',required=True)

     #商城销售明细表
    def _get_data(self,cr, uid, ids, context=None):
        _logger.info("--------------------_get_data start-----------------------------")
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""
       select max(pt.name) as pname,max(pt.t_guid) as t_guid,sum(salecount) as salecount, sum(salefee) as salefee,sum(return_amount) as return_amount,sum(return_payfee) as return_pay,
            sum(gcount) as gcount,sum(gfee) as gfee,sum(expendcount) as expendcount,sum(expendfee) as expendfee,
            sum(givecount) as givecount,sum(givefee) as givefee,sum(scount) as scount,sum(sfee) as sfee,
            max(rp.name) as gname,(case  when max(rp.supplier_mode)='Commission' then '佣金' when max(rp.supplier_mode)='Consign'  then '代售不入仓' when max(rp.supplier_mode)='Direct_Procurement' then '直采'
            when max(rp.supplier_mode)='Consign_stock_in' then '代售入仓' end) as supplier_mode
            from (
            (select sm.product_id,SUM(sq.qty) as salecount,sum(sq.qty*sq.cost) as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,
            0 as givecount,0 as givefee,0 as scount,0 as sfee
            from  stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
            left join sale_order so on so.id=sp.sale_id
            left join stock_location sl on sl.id= sm.location_id
            where  sm.state='done' and spt.code='outgoing'
            and   sm.date between '"""+startdate+"""' and '"""+enddate+"""' and sp.sale_id>0
            and sl.complete_name not like '%Q%'  and sm.picking_type_id not in (365,371)
            group by  sm.product_id)
            UNION ALL
            (
            select sm.product_id, 0 as salecount,0 as salefee,SUM(sq.qty) as return_amount , SUM(sq.qty*sq.cost) as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
            from  stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            left join product_product pp on pp.id=sm.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
            left join sale_order so on so.id=sp.sale_id
            left join ebiz_customer_complain ecc on ecc.order_id=so.id and ecc.product_id=sm.product_id
            where  sm.state='done'
            and sm.date between '"""+startdate+"""' and '"""+enddate+"""'  and sp.picking_type_id =328  and sp.pending=False
            and ecc.type='return_goods' and ecc.state in('closed','over_return_goods','wait_refund')
            group by sm.product_id
            )
            UNION ALL
            (
            select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,SUM(sq.qty) as gcount,SUM(sq.qty*sq.cost) as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
            from stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            where  sm.state='done' and spt.code='outgoing'
            and sm.date between '"""+startdate+"""' and '"""+enddate+"""'  and sp.picking_type_id =251  and sp.origin is null
            group by  sm.product_id
            ) union all
            (
            select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,SUM(sq.qty) as expendcount,SUM(sq.qty*sq.cost) as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
            from  stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            where  sm.state='done' and spt.code='outgoing'
            and   sm.date between '"""+startdate+"""' and '"""+enddate+"""'  and sp.picking_type_id in (369,375)
            group by  sm.product_id
            )
            union all
            (
            select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,SUM(sq.qty) as givecount,SUM(sq.qty*sq.cost) as givefee,0 as scount ,0 as sfee
            from stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            where  sm.state='done' and spt.code='outgoing'
            and sm.date between '"""+startdate+"""' and '"""+enddate+"""'  and sp.picking_type_id in (502,503)
            group by  sm.product_id
            )
            union all
            (
            select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,SUM(sq.qty) as scount,sum(sq.qty*sq.cost) as sfee
            from stock_move sm
            left join stock_picking_type spt on spt.id = sm.picking_type_id
            left join stock_picking sp on sp.id=sm.picking_id
            left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
            left join stock_quant sq on sq.id = sqmr.quant_id
            left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
            left join sale_order so on so.id=sp.sale_id
            where  sm.state='done' and spt.code='outgoing'
            and   sm.date between '"""+startdate+"""' and '"""+enddate+"""'  and sp.picking_type_id in (365,371)
            group by  sm.product_id
            )) a
             left join product_product pp on pp.id=a.product_id
             left join product_template pt on pt.id=pp.product_tmpl_id
             left join product_supplierinfo psu on psu.product_tmpl_id=pt.id
             left join res_partner rp on rp.id=psu.name
            group by  product_id
            order by pname
        """

       #  query="""
       # select max(pt.name) as pname,max(pt.t_guid) as t_guid,sum(salecount) as salecount, sum(salefee) as salefee,sum(return_amount) as return_amount,sum(return_payfee) as return_pay,
       #      sum(gcount) as gcount,sum(gfee) as gfee,sum(expendcount) as expendcount,sum(expendfee) as expendfee,
       #      sum(givecount) as givecount,sum(givefee) as givefee,sum(givefee) as givefee,sum(givefee) as givefee,
       #      max(rp.name) as gname,(case  when max(rp.supplier_mode)='Commission' then '佣金' when max(rp.supplier_mode)='Consign'  then '代售不入仓' when max(rp.supplier_mode)='Direct_Procurement' then '直采'
       #      when max(rp.supplier_mode)='Consign_stock_in' then '代售入仓' end) as supplier_mode
       #      from (
       #      (select sm.product_id,SUM(sq.qty) as salecount,sum(sq.qty*sol.price_unit) as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,
       #      0 as givecount,0 as givefee,0 as scount,0 as sfee
       #      from  stock_move sm
       #      left join stock_picking_type spt on spt.id = sm.picking_type_id
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
       #      left join stock_quant sq on sq.id = sqmr.quant_id
       #      left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
       #      left join sale_order so on so.id=sp.sale_id
       #      left join stock_location sl on sl.id= sm.location_id
       #      where  sm.state='done' and spt.code='outgoing'
       #      and   sm.date between %s and %s and sp.sale_id>0
       #      and sl.complete_name not like '%Q%'
       #      and sm.picking_type_id not in (365,371)
       #      group by  sm.product_id)
       #      UNION ALL
       #      (
       #      select sm.product_id, 0 as salecount,0 as salefee,sum(ecc.return_amount) as return_amount , sum(ecc.return_pay) as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
       #      from  stock_move sm
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join product_product pp on pp.id=sm.product_id
       #      left join product_template pt on pt.id=pp.product_tmpl_id
       #      left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
       #      left join sale_order so on so.id=sp.sale_id
       #      left join ebiz_customer_complain ecc on ecc.order_id=so.id and ecc.product_id=sm.product_id
       #      where  sm.state='done'
       #      and sm.date between %s and %s  and sp.picking_type_id =328  and sp.pending=False
       #      and ecc.type='return_goods' and ecc.state in('closed','over_return_goods','wait_refund')
       #      group by sm.product_id
       #      )
       #      UNION ALL
       #      (
       #      select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,SUM(sq.qty) as gcount,SUM(sq.qty*sq.cost) as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
       #      from stock_move sm
       #      left join stock_picking_type spt on spt.id = sm.picking_type_id
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
       #      left join stock_quant sq on sq.id = sqmr.quant_id
       #      where  sm.state='done' and spt.code='outgoing'
       #      and sm.date between %s and %s  and sp.picking_type_id =251  and sp.origin is null
       #      group by  sm.product_id
       #      ) union all
       #      (
       #      select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,SUM(sq.qty) as expendcount,SUM(sq.qty*sq.cost) as expendfee,0 as givecount,0 as givefee,0 as scount,0 as sfee
       #      from  stock_move sm
       #      left join stock_picking_type spt on spt.id = sm.picking_type_id
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
       #      left join stock_quant sq on sq.id = sqmr.quant_id
       #      where  sm.state='done' and spt.code='outgoing'
       #      and   sm.date between %s and %s  and sp.picking_type_id in (369,375)
       #      group by  sm.product_id
       #      )
       #      union all
       #      (
       #      select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,SUM(sq.qty) as givecount,SUM(sq.qty*sq.cost) as givefee,0 as scount ,0 as sfee
       #      from stock_move sm
       #      left join stock_picking_type spt on spt.id = sm.picking_type_id
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
       #      left join stock_quant sq on sq.id = sqmr.quant_id
       #      where  sm.state='done' and spt.code='outgoing'
       #      and sm.date between %s and %s  and sp.picking_type_id in (502,503)
       #      group by  sm.product_id
       #      )
       #      union all
       #      (
       #      select  sm.product_id,0 as salecount,0 as salefee,0 as return_amount,0 as return_payfee,0 as gcount,0 as gfee,0 as expendcount,0 as expendfee,0 as givecount,0 as givefee,SUM(sq.qty) as scount,sum(sq.qty*sol.price_unit) as sfee
       #      from stock_move sm
       #      left join stock_picking_type spt on spt.id = sm.picking_type_id
       #      left join stock_picking sp on sp.id=sm.picking_id
       #      left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
       #      left join stock_quant sq on sq.id = sqmr.quant_id
       #      left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
       #      left join sale_order so on so.id=sp.sale_id
       #      where  sm.state='done' and spt.code='outgoing'
       #      and   sm.date between %s and %s  and sp.picking_type_id in (365,371)
       #      group by  sm.product_id
       #      )) a
       #       left join product_product pp on pp.id=a.product_id
       #       left join product_template pt on pt.id=pp.product_tmpl_id
       #       left join product_supplierinfo psu on psu.product_tmpl_id=pt.id
       #       left join res_partner rp on rp.id=psu.name
       #      group by  product_id
       #      order by pname
       #  """
        _logger.info("--------------------query-----------------------------")
        # logging.info(query)
        cr.execute(query)
        # cr.execute(query,([startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate]))
        data = cr.fetchall()
        _logger.info("--------------------_get_data end-----------------------------")
        return data

    def button_export(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'商城销成本售明细表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'商城销售成本明细表.xls',
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



    #商城销售明细表
    def from_data(self, cr, uid, ids, context=None):
        _logger.info("--------------------from_data start-----------------------------")
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'商城销售成本明细表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'商城销售明细表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 16, worksheet_header)
                worksheet.write(1, 0, u'物品名称', content_title)
                worksheet.write(1, 1, u'物品编码', content_title)
                worksheet.write(1, 2, u'销售出库数量', content_title)
                worksheet.write(1, 3, u'销售出库成本金额', content_title)
                worksheet.write(1, 4, u'销售退货数量', content_title)
                worksheet.write(1, 5, u'销售退货成本金额', content_title)
                worksheet.write(1, 6, u'代销供应商退货数量', content_title)# 退给供应商的数量
                worksheet.write(1, 7, u'代销供应商退货成本金额', content_title)
                worksheet.write(1, 8, u'借料消耗数量', content_title)
                worksheet.write(1, 9, u'借料消耗成本金额', content_title)
                worksheet.write(1, 10, u'借料赠送数量', content_title)
                worksheet.write(1, 11, u'借料赠送成本金额', content_title)
                worksheet.write(1, 12, u'借料销售数量', content_title)
                worksheet.write(1, 13, u'借料销售成本金额', content_title)
                worksheet.write(1, 14, u'供应商名称', content_title)
                worksheet.write(1, 15, u'供应商类别', content_title)

                index = 1
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
                    index += 1
            fp = StringIO()
            workbook.save( fp )
            fp.seek( 0 )
            excel = fp.read()
            fp.close()
            _logger.info("--------------------from_data end-----------------------------")
            return excel
