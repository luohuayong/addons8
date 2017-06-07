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

class ebiz_supplier_account_line_excel(models.TransientModel):
    _name = 'ebiz.supplier.account.line.excel'
    startdate=fields.Datetime(u'开始日期',required=True)
    enddate=fields.Datetime(u'结束日期',required=True)


    def _get_data(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select * from (
                    select a.*,b.采购金额 as 费用扣款 from (
                    select rp.name,(case  when rp.supplier_mode='Commission' then '佣金' when rp.supplier_mode='Consign'  then '代售不入仓' when rp.supplier_mode='Direct_Procurement' then '直采' when rp.supplier_mode='Consign_stock_in' then '代售入仓' end) as 供应商类型,COALESCE(esal.statement_no,'') as statement_no
                    ,(case when max(esal.state)='settled' then '已结算' when max(esal.state)='draft' then '未对账' when max(esal.state)='checked' then '已对账' else '已取消' end) as 状态
                    ,sum(esal.subtotal) as 销售金额,sum(esal.purchase_total) as 采购金额,sum(esal.commission) as 佣金  from ebiz_supplier_account_line   esal
                    left join res_partner rp on esal.partner_id =rp.id
                    where esal.qty_send>=%s and esal.qty_send<=%s  and esal.type in ('payment_goods','return_goods') and  esal.state!='cancelled'

                    group by rp.name,rp.supplier_mode,COALESCE(esal.statement_no,'')
                    ) a
                    left join
                    (
                    select rp.name,(case  when rp.supplier_mode='Commission' then '佣金' when rp.supplier_mode='Consign'  then '代售不入仓' when rp.supplier_mode='Direct_Procurement' then '直采' when rp.supplier_mode='Consign_stock_in' then '代售入仓' end) as 供应商类型,COALESCE(esal.statement_no,'') as statement_no

                    ,sum(esal.subtotal) as 销售金额,sum(esal.purchase_total) as 采购金额,sum(esal.commission) as 佣金  from ebiz_supplier_account_line   esal

                    left join res_partner rp on esal.partner_id =rp.id


                    where esal.qty_send>=%s and esal.qty_send<=%s and esal.type='cost' and esal.state!='cancelled'

                    group by rp.name,rp.supplier_mode,COALESCE(esal.statement_no,'')
                    ) b on a.name=b.name and a.供应商类型=b.供应商类型 and a.statement_no=b.statement_no

                    union
                    select * from (
                    select rp.name,(case  when rp.supplier_mode='Commission' then '佣金' when rp.supplier_mode='Consign'  then '代售不入仓' when rp.supplier_mode='Direct_Procurement' then '直采' when rp.supplier_mode='Consign_stock_in' then '代售入仓' end) as 供应商类型,
                    COALESCE(esal.statement_no,'') as statement_no,(case when max(esal.state)='settled' then '已结算' when max(esal.state)='draft' then '未对账' when max(esal.state)='checked' then '已对账' else '已取消' end) as 状态
                    ,0 销售金额,0 as 采购金额,0 as 佣金,sum(esal.purchase_total) as 费用扣款  from ebiz_supplier_account_line esal
                    left join res_partner rp on esal.partner_id =rp.id
                    where esal.qty_send>=%s and esal.qty_send<=%s and esal.type='cost' and esal.state!='cancelled'
                    group by rp.name,rp.supplier_mode,COALESCE(esal.statement_no,'')
                    ) d where d.name||'|'|| COALESCE(d.statement_no,'') not in (
                    select e.name||'|'|| COALESCE(e.statement_no,'') from (
                    select COALESCE(esal.statement_no,'') as statement_no ,rp.name  from ebiz_supplier_account_line esal
                    left join res_partner rp on esal.partner_id =rp.id
                    where esal.qty_send>=%s and esal.qty_send<=%s and esal.type in ('payment_goods','return_goods') and esal.state!='cancelled'
                    group by rp.id ,COALESCE(esal.statement_no,''))e
                    )
                    )  c     order by name

                    """
        cr.execute(query,([startdate, enddate,startdate, enddate,startdate, enddate,startdate, enddate]))
        data = cr.fetchall()
        return data






    def from_data(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'供应商结算单汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'供应商结算单汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 6, worksheet_header)
                worksheet.write(1, 0, u'供应商名称', content_title)
                worksheet.write(1, 1, u'供应商类型', content_title)
                worksheet.write(1, 2, u'对账单单号', content_title)
                worksheet.write(1, 3, u'状态', content_title)
                worksheet.write(1, 4, u'销售金额', content_title)
                worksheet.write(1, 5, u'采购金额', content_title)
                worksheet.write(1, 6, u'佣金', content_title)
                worksheet.write(1, 7, u'费用扣款', content_title)

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
                    index += 1
            fp = StringIO()
            workbook.save( fp )
            fp.seek( 0 )
            excel = fp.read()
            fp.close()
            return excel

        #佣金供应商结算单汇总表
    def button_export(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'佣金供应商结算单汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':'ebiz_supplier_account_line.xls',
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