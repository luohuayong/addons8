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

class sale_income_total(models.TransientModel):
    _name = 'sale.income.total'
    startdate=fields.Datetime(u'开始日期',required=True)
    enddate=fields.Datetime(u'结束日期',required=True)
    def from_data(self, cr, uid, ids, context=None):
        if context:
            data=self._get_data(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'订单')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            if (worksheet):
                worksheet.write(0, 0, u'订单号', content_title)
                worksheet.write(0, 1, u'订单状态', content_title)
                worksheet.write(0, 2, u'创建时间', content_title)
                worksheet.write(0, 3, u'签收时间', content_title)
                worksheet.write(0, 4, u'出库时间', content_title)
                worksheet.write(0, 5, u'订单总金额', content_title)
                worksheet.write(0, 6, u'优惠转让', content_title)
                worksheet.write(0, 7, u'运费', content_title)
                worksheet.write(0, 8, u'实际支付金额', content_title)
                worksheet.write(0, 9, u'供应商类型', content_title)
                worksheet.write(0, 10, u'仓库', content_title)
                worksheet.write(0, 11, u'供应商', content_title)
                worksheet.write(0, 12, u'支付方式', content_title)
                worksheet.write(0, 13, u'支付流水号', content_title)
                worksheet.write(0, 14, u'是否发货', content_title)


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
                    index += 1
            # except Exception, ex:
            #     _logger.info(Exception, ":", ex)
            fp = StringIO()
            workbook.save( fp )
            fp.seek( 0 )
            excel = fp.read()
            fp.close()
            return excel

    def from_data_refund(self, cr, uid, ids, context=None):
        if context:
            data=self._get_data_refund(cr, uid, ids, context=None)
            logging.info("-------------------------------------")
            logging.info(len(data))
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'退款明细')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            if (worksheet):
                worksheet.write(0, 0, u'订单号', content_title)
                worksheet.write(0, 1, u'退款商品', content_title)
                worksheet.write(0, 2, u'客诉单号', content_title)
                worksheet.write(0, 3, u'日期', content_title)
                worksheet.write(0, 4, u'实际退款金额', content_title)
                worksheet.write(0, 5, u'最大退款金额', content_title)
                worksheet.write(0, 6, u'商品总价', content_title)
                worksheet.write(0, 7, u'供应商', content_title)
                worksheet.write(0, 8, u'供应商类型', content_title)
                worksheet.write(0, 9, u'支付方式', content_title)
                worksheet.write(0, 10, u'支付流水号', content_title)

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
        excel = base64.encodestring(self.from_data(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'订单收入_'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
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

    #导出退款明细
    def button_export_refund(self, cr, uid, ids, context=None):

        excel = base64.encodestring(self.from_data_refund(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'退款明细_'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':'refund.xls',
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

    def _get_data_refund(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        # query="""
        #  select amount as 退款金额,date as 退款日期,reference as 退款流水号 from account_voucher where sale_order_id>0 and   date>=%s and date <= %s
        # """

        # query="""
        #         select so.name as 订单号,(av.create_date+ '8H') as 退款时间, av.amount as 退款金额,av.reference as 退款流水号, ( case when a.supplier_mode='Direct_Procurement' then '直采'  when a.supplier_mode='Commission' then '佣金'
        #          when a.supplier_mode='Consign' then '代售不入仓'  when a.supplier_mode='Consign_stock_in' then '代售入仓' end) as供应商类型 ,
        #
        #         aj.name as 支付方式,spl.ref as 支付流水号 from account_voucher  av
        #
        #         left join sale_order so on av.sale_order_id = so.id
        #
        #         left join
        #
        #         (
        #         select sol1.order_id,max(rp.id) as supplierid,max(rp.name) as suppliername,max(rp.supplier_mode) as supplier_mode from  sale_order_line sol1
        #             left join product_product pp1 on pp1.id=sol1.product_id
        #             left join product_template pt1 on pt1.id=pp1.product_tmpl_id
        #             left join  product_supplierinfo ps on pt1.id=ps.product_tmpl_id
        #             left join res_partner rp on rp.id=ps.name
        #             left join  stock_warehouse sw on rp.stock_warehouse_id=sw.id
        #             where pt1.type!='service'
        #             group by sol1.order_id
        #         ) a on a.order_id=av.sale_order_id
        #
        #         left join sale_payment_line spl on spl.order_id=so.id
        #         left join account_journal aj on aj.id=spl.journal_id
        #
        #         where sale_order_id>0  and   av.create_date>=%s and av.create_date <= %s
        #  """
        query="""
        select  so.name as 订单号,pt.name as 退货商品,ecc.name as 客诉单号,(aml.create_date+ '8H') as create_date, aml.debit as 退款金额, sol.rebateprice as 最大退款金额,sol.product_uom_qty*sol.price_unit 商品总价,rp.name as 供应商,( case when rp.supplier_mode='Direct_Procurement' then '直采'  when rp.supplier_mode='Commission' then '佣金'
                 when rp.supplier_mode='Consign' then '代售不入仓'  when rp.supplier_mode='Consign_stock_in' then '代售入仓' end) as 供应商类型,
                aj.name as 支付方式,spl.ref as 支付流水号 from account_move_line aml

                right join
                (
                    select (ml.create_date+ '8H') as create_date, reconcile_id,reconcile_partial_id,i.id,ml.id as mid, i.amount_total From account_move_line ml
                    inner JOIN account_move m on ml.move_id = m.id
                    inner join account_invoice i on i.move_id = m.id  and i.account_id = ml.account_id and i.state='paid'  and i.type='out_refund'

                ) a on (aml.reconcile_id =a.reconcile_id or aml.reconcile_partial_id=a.reconcile_partial_id) and aml.id!=a. mid

                left join  account_invoice i on a.id=i.id
                left join ebiz_customer_complain ecc on ecc.name=i.origin
                left join sale_order so on ecc.order_id = so.id
                left join sale_payment_line spl on spl.order_id=so.id
                left join account_journal aj on aj.id=spl.journal_id

                left join sale_order_line sol on sol.order_id=so.id and sol.product_id=ecc.product_id
                left join product_product pp on pp.id=sol.product_id and pp.id=ecc.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id and pt.type!='service'
                left join  product_supplierinfo ps on pt.id=ps.product_tmpl_id
                left join res_partner rp on rp.id=ps.name

                where aml.create_date>=%s and aml.create_date <= %s

                order by create_date
        """
        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        _logger.info(data)
        return data

#so.total_fee as 订单总金额,
    def _get_data(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select  so.name as 订单号,
(case when so.state='cancel' then '已取消' when so.state='progress' then '销售订单' when so.state='manual' then '销售待开票' when so.state='shipping_except' then '送货异常' when so.state='invoice_exception' then '发票异常' when so.state='draft' then '未审核订单' when so.state='done' then '已完成' end ) as 订单状态
 , (so.date_order + '8 H') as create_date,  (so.sign_date + '8 H') as 签收时间,(move.date+'8 H') as 出库时间,(so.total_fee-COALESCE(yf.yf,0)) as 订单总金额,COALESCE(yh.yjjk,0) as 优惠折让,COALESCE(yf.yf,0) as 邮费,so.amount_total as 实际支付金额,
(case  when rp.supplier_mode='Commission' then '佣金' else  '非佣金' end) as 供应商类型
,sw.name as 供应商仓库,rp.name as 供应商 ,aj.name as 支付方式,spl.ref as 支付流水号,(case when so.shipped='t' then '已发货' when so.shipped='f' then '未发货' end) as 是否发货
from sale_order  so
left join
(
select sol1.order_id, sol1.price_unit*product_uom_qty as yjjk from  sale_order_line sol1
left join product_product pp1 on pp1.id=sol1.product_id
left join product_template pt1 on pt1.id=pp1.product_tmpl_id
where pp1.default_code='yhjm' and  pt1.type='service'
) yh on yh.order_id=so.id

left join
(
select sol2.order_id, sol2.price_unit*product_uom_qty as yf from  sale_order_line sol2
left join product_product pp2 on pp2.id=sol2.product_id
left join product_template pt2 on pt2.id=pp2.product_tmpl_id
where pp2.default_code='yf' and  pt2.type='service'
) yf on yf.order_id=so.id

left join
(
select max(pt.id) as id,sol1.order_id from sale_order_line sol1
left join product_product pp on sol1.product_id =pp.id
left join product_template pt on pt.id=pp.product_tmpl_id
where   pt.type!='service'
group by sol1.order_id
) pro  on pro.order_id=so.id

left join product_supplierinfo ps on pro.id=ps.product_tmpl_id
left join res_partner rp on rp.id=ps.name
left join  stock_warehouse sw on rp.stock_warehouse_id=sw.id


left join sale_payment_line spl on spl.order_id=so.id
left join account_journal aj on aj.id=spl.journal_id

left join
(
select sm.origin,max(sm.date) as date  from  stock_move  sm
left join stock_picking_type spt on spt.id = sm.picking_type_id
left join stock_picking sp on sp.id=sm.picking_id
left join  product_product pp on  sm.product_id=pp.id
where sm.state='done' and spt.code='outgoing'
group by sm.origin
) move on move.origin=so.name

where  (so.date_order>=%s and so.date_order <=%s) or (move.date>=%s and move.date <=%s)
order by create_date
"""
        cr.execute(query,([startdate, enddate,startdate, enddate]))
        data = cr.fetchall()
        return data