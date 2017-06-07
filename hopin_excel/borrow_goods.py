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
class borrow_goods(models.TransientModel):
    _name = 'borrow.goods'
    startdate=fields.Datetime(u'开始日期',required=True)
    enddate=fields.Datetime(u'结束日期',required=True)

    #借料汇总表
    def _get_data(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
                    from stock_move sm
                    left join stock_picking_type spt on spt.id = sm.picking_type_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
                    left join stock_quant sq on sq.id = sqmr.quant_id

                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join res_partner rp on rp.id=sp.partner_id
                    left join stock_location sl on sl.id= sm.location_dest_id


                    where  sm.state='done' and spt.code='outgoing'
                    and sm.date between  %s and %s and sp.picking_type_id in (377,379,1111)
                    group by  sm.product_id,sq.cost,sp.name
                    order by pname
                    """
        # query="""
        # select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
        #             from stock_move sm
        #             left join stock_picking_type spt on spt.id = sm.picking_type_id
        #             left join stock_picking sp on sp.id=sm.picking_id
        #             left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
        #             left join stock_quant sq on sq.id = sqmr.quant_id
        #
        #             left join product_product pp on pp.id=sm.product_id
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             left join res_partner rp on rp.id=sp.partner_id
        #             left join stock_location sl on sl.id= sm.location_dest_id
        #
        #
        #             where  sm.state='done' and spt.code='outgoing'
        #             and sm.date between  %s and %s and sp.picking_type_id in (377,379,1139,1199,1200,1201,1202,1203,1204,1205,1206,1207)
        #             group by  sm.product_id,sq.cost,sp.name
        #             order by location
        # """
        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        return data





    #借料汇总表
    def from_data(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'借料汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'借料汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 8, worksheet_header)
                worksheet.write(1, 0, u'产品', content_title)
                worksheet.write(1, 1, u'单据编号', content_title)
                worksheet.write(1, 2, u'目的位置', content_title)
                worksheet.write(1, 3, u'业务伙伴', content_title)
                worksheet.write(1, 4, u'借料数量', content_title)
                worksheet.write(1, 5, u'成本价', content_title)
                worksheet.write(1, 6, u'金额', content_title)
                worksheet.write(1, 7, u'日期', content_title)

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

        #借料汇总表
    def button_export(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'借料汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'借料汇总表.xls',
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

    #赠送汇总表
    def button_export1(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data1(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'赠送汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'赠送汇总表.xls',
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

        #赠送汇总表
    def _get_data1(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
                    from stock_move sm
                    left join stock_picking_type spt on spt.id = sm.picking_type_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
                    left join stock_quant sq on sq.id = sqmr.quant_id

                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join res_partner rp on rp.id=sp.partner_id
                    left join stock_location sl on sl.id= sm.location_id


                    where  sm.state='done' and spt.code='outgoing'
                    and sm.date between  %s and %s and sp.picking_type_id in (502,503,1113)
                    group by  sm.product_id,sq.cost,sp.name
                    order by pname
                    """
        # query="""
        #     select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
        #             from stock_move sm
        #             left join stock_picking_type spt on spt.id = sm.picking_type_id
        #             left join stock_picking sp on sp.id=sm.picking_id
        #             left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
        #             left join stock_quant sq on sq.id = sqmr.quant_id
        #
        #             left join product_product pp on pp.id=sm.product_id
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             left join res_partner rp on rp.id=sp.partner_id
        #             left join stock_location sl on sl.id= sm.location_id
        #
        #
        #             where  sm.state='done' and spt.code='outgoing'
        #             and sm.date between  %s and %s and sp.picking_type_id in (502,503,1142,1217,1218,1219,1220,1221,1222,1223,1224,1225)
        #             group by  sm.product_id,sq.cost,sp.name
        #             order by location
        # """
        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        return data





    #赠送汇总表
    def from_data1(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data1(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'赠送汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'赠送汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 8, worksheet_header)
                worksheet.write(1, 0, u'产品', content_title)
                worksheet.write(1, 1, u'单据编号', content_title)
                worksheet.write(1, 2, u'源位置', content_title)
                worksheet.write(1, 3, u'业务伙伴', content_title)
                worksheet.write(1, 4, u'数量', content_title)
                worksheet.write(1, 5, u'成本价', content_title)
                worksheet.write(1, 6, u'金额', content_title)
                worksheet.write(1, 7, u'日期', content_title)

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

    #消耗汇总表
    def button_export2(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data2(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'消耗汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'消耗汇总表.xls',
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

        #消耗汇总表
    def _get_data2(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
                    from stock_move sm
                    left join stock_picking_type spt on spt.id = sm.picking_type_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
                    left join stock_quant sq on sq.id = sqmr.quant_id

                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join res_partner rp on rp.id=sp.partner_id
                    left join stock_location sl on sl.id= sm.location_id


                    where  sm.state='done' and spt.code='outgoing'
                    and sm.date between  %s and %s and sp.picking_type_id in (369,375,1114)
                    group by  sm.product_id,sq.cost,sp.name
                    order by pname
                    """
        # query="""
        #     select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
        #             from stock_move sm
        #             left join stock_picking_type spt on spt.id = sm.picking_type_id
        #             left join stock_picking sp on sp.id=sm.picking_id
        #             left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
        #             left join stock_quant sq on sq.id = sqmr.quant_id
        #
        #             left join product_product pp on pp.id=sm.product_id
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             left join res_partner rp on rp.id=sp.partner_id
        #             left join stock_location sl on sl.id= sm.location_id
        #
        #
        #             where  sm.state='done' and spt.code='outgoing'
        #             and sm.date between  %s and %s and sp.picking_type_id in (369,375,1141,1226,1227,1228,1229,1230,1231,1232,1233,1234)
        #             group by  sm.product_id,sq.cost,sp.name
        #             order by location
        # """


        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        return data





    #消耗汇总表
    def from_data2(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data2(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'消耗汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'消耗汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 8, worksheet_header)
                worksheet.write(1, 0, u'产品', content_title)
                worksheet.write(1, 1, u'单据编号', content_title)
                worksheet.write(1, 2, u'源位置', content_title)
                worksheet.write(1, 3, u'业务伙伴', content_title)
                worksheet.write(1, 4, u'数量', content_title)
                worksheet.write(1, 5, u'成本价', content_title)
                worksheet.write(1, 6, u'金额', content_title)
                worksheet.write(1, 7, u'日期', content_title)

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



        #销售汇总表
    def button_export3(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data3(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'销售汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'销售汇总表.xls',
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

        #销售汇总表
    def _get_data3(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""
            select max(pt.name) as pname,sp.name,so.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,max(sol.price_unit) as price_unit,sum(sol.product_uom_qty*sol.price_unit) as salefee,   sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
                    from stock_move sm
                    left join stock_picking_type spt on spt.id = sm.picking_type_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
                    left join stock_quant sq on sq.id = sqmr.quant_id

                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join res_partner rp on rp.id=sp.partner_id
                    left join stock_location sl on sl.id= sm.location_id

		           left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
		           left join sale_order so on so.id=sp.sale_id

                    where  sm.state='done' and spt.code='outgoing'
                    and   sm.date between  %s and %s and sp.picking_type_id in (365,371,1107)
                    group by  sm.product_id,sq.cost,sp.name,so.name
                    order by pname
                    """
        # query="""
        # select max(pt.name) as pname,sp.name,so.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,max(sol.price_unit) as price_unit,sum(sol.product_uom_qty*sol.price_unit) as salefee,   sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
        #         from stock_move sm
        #         left join stock_picking_type spt on spt.id = sm.picking_type_id
        #         left join stock_picking sp on sp.id=sm.picking_id
        #         left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
        #         left join stock_quant sq on sq.id = sqmr.quant_id
        #
        #         left join product_product pp on pp.id=sm.product_id
        #         left join product_template pt on pt.id=pp.product_tmpl_id
        #         left join res_partner rp on rp.id=sp.partner_id
        #         left join stock_location sl on sl.id= sm.location_id
        #
        #         left join sale_order_line sol on sol.order_id=sp.sale_id and sol.product_id=sm.product_id
        #         left join sale_order so on so.id=sp.sale_id
        #
        #         where  sm.state='done' and spt.code='outgoing'
        #         and   sm.date between  %s and %s and sp.picking_type_id in (365,371,1135,1145,1150,1155,1160,1165,1170,1175,1180,1185)
        #         group by  sm.product_id,sq.cost,sp.name,so.name
        #         order by location
        #         """
        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        return data


    #销售汇总表
    def from_data3(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data3(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'销售汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'销售汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 11, worksheet_header)
                worksheet.write(1, 0, u'产品', content_title)
                worksheet.write(1, 1, u'单据编号', content_title)
                worksheet.write(1, 2, u'订单号', content_title)
                worksheet.write(1, 3, u'源位置', content_title)
                worksheet.write(1, 4, u'业务伙伴', content_title)
                worksheet.write(1, 5, u'数量', content_title)
                worksheet.write(1, 6, u'销售价', content_title)
                worksheet.write(1, 7, u'销售金额', content_title)
                worksheet.write(1, 8, u'成本价', content_title)
                worksheet.write(1, 9, u'成本金额', content_title)
                worksheet.write(1, 10, u'日期', content_title)

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
                    index += 1
            fp = StringIO()
            workbook.save( fp )
            fp.seek( 0 )
            excel = fp.read()
            fp.close()
            return excel



            #借料还料汇总表

#还料汇总表



    #还料汇总表
    def _get_data4(self,cr, uid, ids, context=None):
        sit=self.browse(cr, uid, ids[0], context=context)
        startdate=sit.startdate
        enddate=sit.enddate
        query="""select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
                    from stock_move sm
                    left join stock_picking_type spt on spt.id = sm.picking_type_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
                    left join stock_quant sq on sq.id = sqmr.quant_id

                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join res_partner rp on rp.id=sp.partner_id
                    left join stock_location sl on sl.id= sm.location_id


                    where  sm.state='done' and spt.code='incoming'
                    and sm.date between  %s and %s and sp.picking_type_id in (380,378,1112)
                    group by  sm.product_id,sq.cost,sp.name
                    order by pname
                    """
        # query="""select max(pt.name) as pname,sp.name,max(sl.complete_name) as location,max(rp.name) as uname,SUM(sq.qty) as count,sq.cost,SUM(sq.qty*sq.cost) as totalfee,max(sm.date+'8 H') as date
        #             from stock_move sm
        #             left join stock_picking_type spt on spt.id = sm.picking_type_id
        #             left join stock_picking sp on sp.id=sm.picking_id
        #             left join stock_quant_move_rel sqmr on sqmr.move_id = sm.id
        #             left join stock_quant sq on sq.id = sqmr.quant_id
        #
        #             left join product_product pp on pp.id=sm.product_id
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             left join res_partner rp on rp.id=sp.partner_id
        #             left join stock_location sl on sl.id= sm.location_id
        #
        #
        #             where  sm.state='done' and spt.code='incoming'
        #             and sm.date between  %s and %s and sp.picking_type_id in (380,378,1140,1208,1209,1210,1211,1212,1213,1214,1215,1216)
        #             group by  sm.product_id,sq.cost,sp.name
        #             order by location
        #             """
        cr.execute(query,([startdate, enddate]))
        data = cr.fetchall()
        return data





    #还料汇总表
    def from_data4(self, cr, uid, ids, context=None):
        if context:
            sit=self.browse(cr, uid, ids[0], context=context)
            startdate= str(datetime.datetime.strptime(sit.startdate, "%Y-%m-%d %H:%M:%S")+ datetime.timedelta(1))[0:10]
            enddate=sit.enddate[0:10]
            data=self._get_data4(cr, uid, ids, context=None)
            # if data:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet(u'还料汇总表')
            header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
            order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )
            content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
            # try:
            worksheet_header=u'还料汇总表'+'('+startdate+'~'+enddate+')'
            if (worksheet):
                worksheet.write_merge(0,0,0, 8, worksheet_header)
                worksheet.write(1, 0, u'产品', content_title)
                worksheet.write(1, 1, u'单据编号', content_title)
                worksheet.write(1, 2, u'源位置', content_title)
                worksheet.write(1, 3, u'业务伙伴', content_title)
                worksheet.write(1, 4, u'数量', content_title)
                worksheet.write(1, 5, u'成本价', content_title)
                worksheet.write(1, 6, u'金额', content_title)
                worksheet.write(1, 7, u'日期', content_title)

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

        #还料汇总表
    def button_export4(self, cr, uid, ids, context=None):
        excel = base64.encodestring(self.from_data4(cr, uid, ids, context))
        ts_obj = self.browse(cr, uid, ids, context=context)

        attach_vals = {
                 'name':u'还料汇总表'+ts_obj.startdate+'-'+ts_obj.enddate+'.xls',
                 'datas':excel,
                 'datas_fname':u'还料汇总表.xls',
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