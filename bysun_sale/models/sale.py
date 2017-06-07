# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, osv
import logging
import json
import time,datetime
try:
    import xlwt
except ImportError:
    xlwt = None
import base64
from cStringIO import StringIO

_logger = logging.getLogger(__name__)


class sale_order_batch_confirm(models.Model):
    _name = 'sale.order.batch.confirm'

    def batch_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        order_obj = self.pool.get('sale.order')
        for sale_order in order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if sale_order.state != 'draft':
                raise osv.except_osv(_('Warning!'), _("订单 %s 不是草稿状态!") % (sale_order.name))
            result = order_obj.action_button_confirm(cr, uid, [sale_order.id], context=context)
        return result

class sale_order_export_to_supplier_line(models.Model):
    _name = 'sale.order.export.to.supplier.line'

    export_id = fields.Many2one('sale.order.export.to.supplier', u'导出编码', required=True)
    order_no = fields.Char(u'自定义单号', required=True)
    product_no = fields.Char(u'商品编码')
    product_uom_qty = fields.Float(u'数量')
    partner_shipping_id = fields.Many2one('res.partner', u'收货人')
    receiver = fields.Char(u'收货人姓名')
    mobile = fields.Char(u'手机号码')
    receiver_area = fields.Char(u'收货区域')
    receiver_addr = fields.Char(u'详细地址')
    phone = fields.Char(u'固定电话')
    receiver_IDCard = fields.Char(u'身份证号码')
    zip = fields.Char(u'邮政编码')
    buyer_memo = fields.Text(u'订单备注')



class sale_order_export_to_supplier(models.Model):
    _name = 'sale.order.export.to.supplier'

    partner_id = fields.Many2one('res.partner', u'供应商', required=True)
    start_order_date = fields.Datetime(u'订单开始时间', required=True)
    end_order_date = fields.Datetime(u'订单结束时间', required=True)
    order_lines = fields.One2many('sale.order.export.to.supplier.line', 'export_id', u'订单明细')

    def button_query(self, cr, uid, ids, context=None):

        context = context or {}
        ts_obj = self.browse(cr, uid, ids, context=context)
        # if not ts_obj.end_order_date:
        #     ts_obj.end_order_date = datetime.datetime.now() - datetime.timedelta(hours=8)

        lines = []
        for line in ts_obj.order_lines:
            lines.append((2, line.id, 0))
        ts_obj.write({'order_lines': lines})


        query = """
            select SO.name, pt.product_psn, sol.product_uom_qty, SO.partner_shipping_id, rp1.name, rp1.mobile, rcs.name , rp1.city, rp1.street, rp1.phone, rp2.code, rp1.zip, so.note, rp1.street2
                From sale_order_line sol
                    left join sale_order so on sol.order_id = so.id
                    left join product_product pp on sol.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id
                        left join product_supplierinfo ps on ps.product_tmpl_id = pp.product_tmpl_id
                        left join res_partner rp on ps.name = rp.id
                        left join res_partner rp1 on so.partner_shipping_id = rp1.id
                            left join res_country_state rcs on rp1.state_id = rcs.id
                    left join res_partner rp2 on so.partner_id = rp2.id
                where rp.id = %s and so.date_order >= %s and so.date_order < %s
                order by so.name
        """
        cr.execute(query, ([ts_obj.partner_id.id, ts_obj.start_order_date, ts_obj.end_order_date]))
        data = cr.fetchall()
        lines = []
        for row in data:
            line = {
                'order_no': row[0],
                'product_no': row[1],
                'product_uom_qty': row[2],
                'partner_shipping_id': row[3],
                'receiver': row[4],
                'mobile': row[5],
                'receiver_area': row[6] + '-' + row[7] + '-' + row[13],
                'receiver_addr': row[8],
                'phone': row[9],
                'receiver_IDCard': row[10],
                'zip': row[11],
                'buyer_memo': row[12]
            }
            lines.append((0, 0, line))
        result = ts_obj.write({'order_lines': lines})
        return result


    def from_data(self, cr, uid, ids, context=None):
        workbook = xlwt.Workbook()

        ts_obj = self.browse(cr, uid, ids, context=context)

        header_title = xlwt.easyxf( "font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
        header_subtitle = xlwt.easyxf( "font: bold on,height 300; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
        order_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal center, indent 1,vertical center" )
        order_title_col = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour green;align:horizontal right, indent 1,vertical center" )

        content_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )


        worksheet = workbook.add_sheet(u'订单')
        try:
            if (worksheet):
                #worksheet.insert_bitmap('http://localhost:8069/web/binary/company_logo?db=XLD&amp;company=1', 0, 0)
                worksheet.write(0, 0, u'自定义单号', content_title)
                worksheet.write(0, 1, u'商品编号', content_title)
                worksheet.write(0, 2, u'数量', content_title)
                worksheet.write(0, 3, u'收货人姓名', content_title)
                worksheet.write(0, 4, u'手机号码', content_title)
                worksheet.write(0, 5, u'收货区域', content_title)
                worksheet.write(0, 6, u'详细地址', content_title)
                worksheet.write(0, 7, u'固定电话', content_title)
                worksheet.write(0, 8, u'身份证号码', content_title)
                worksheet.write(0, 9, u'邮政编码', content_title)
                worksheet.write(0, 10, u'是否购买保险', content_title)
                worksheet.write(0, 11, u'是否包装加固', content_title)
                worksheet.write(0, 12, u'订单备注', content_title)

                index = 0
                startRow = 1
                ids = []
                for line in ts_obj.order_lines:
                    ids.append(line.id)
                for line in self.pool.get('sale.order.export.to.supplier.line').browse(cr, uid, ids, context):
                    if line.order_no:
                        worksheet.write(startRow + index, 0, line.order_no, content_title)
                    if line.product_no:
                        worksheet.write(startRow + index, 1, line.product_no + ' ', content_title)
                    if line.product_uom_qty:
                        worksheet.write(startRow + index, 2, line.product_uom_qty, content_title)
                    if line.receiver:
                        worksheet.write(startRow + index, 3, line.receiver, content_title)
                    if line.mobile:
                        worksheet.write(startRow + index, 4, line.mobile, content_title)
                    if line.receiver_area:
                        worksheet.write(startRow + index, 5, line.receiver_area, content_title)
                    if line.receiver_addr:
                        worksheet.write(startRow + index, 6, line.receiver_addr, content_title)
                    if line.phone and line.phone[0:1] == '0':
                        worksheet.write(startRow + index, 7, line.phone, content_title)
                    if line.receiver_IDCard:
                        worksheet.write(startRow + index, 8, line.receiver_IDCard + ' ', content_title)
                    if line.zip:
                        worksheet.write(startRow + index, 9, line.zip, content_title)
                    worksheet.write(startRow + index, 10, u'否', content_title)
                    worksheet.write(startRow + index, 11, u'否', content_title)
                    if line.buyer_memo:
                        worksheet.write(startRow + index, 12, line.buyer_memo, content_title)
                    index += 1

        except Exception, ex:
            print Exception, ":", ex

        fp = StringIO()
        workbook.save( fp )
        fp.seek( 0 )
        data = fp.read()
        fp.close()
        return data

    def button_export(self, cr, uid, ids, context=None):
        data = base64.encodestring( self.from_data(cr, uid, ids, None))

        ts_obj = self.browse(cr, uid, ids, context=context)
        rp_obj = self.pool.get('res.partner').browse(cr, uid, [ts_obj.partner_id.id], context=context)

        attach_vals = {
                 'name':u'供应商_' + rp_obj.name + '_' + ts_obj.start_order_date + '_' + ts_obj.end_order_date + '.xls',
                 'datas':data,
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


class sale_order(models.Model):
    _inherit = 'sale.order'

    delivery_code = fields.Char(u'配送编码', help=u'对应网站的id字段')
    delivery_date = fields.Date(u'配送日期', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    delivery_hour = fields.Char(u'配送时段', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    is_cod = fields.Boolean(string=u'是否是货到付款')
    is_distribution = fields.Boolean(string=u'是否分销')
    distribution_name = fields.Char(string=u'分销渠道名称')
    distribution_detail = fields.Selection([('dis1','10'),('ids2','15')],string=u'分销详情')
    is_selfsupport = fields.Boolean(u'是否为主仓发货')

    parent_order_no = fields.Char(u'父订单编号')
    sign_date = fields.Datetime(u'签收时间')
    seller_memo = fields.Text(u'卖家备注')

    def is_ec_order(self, cr, uid, ids, context=None):
        pass
        return True

    def select_delivery_hour(self, cr, uid, ids, context=None):
        return True

    def buyer_sign(self, cr, uid, sign_info, context=None):
        result = {}
        context = context or {}
        _logger.info(sign_info)

        if sign_info.get('order_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少订单编号参数!'})
            _logger.info(result)
            return result
        if sign_info.get('sign_date', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少签收时间参数!'})
            _logger.info(result)
            return result

        so_ids = self.search(cr, uid, [('name', '=', sign_info['order_no'])], context=context)
        so_id = len(so_ids) and so_ids[0] or False
        if not so_id:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编号的订单: %s!'%sign_info['order_no']})
            _logger.info(result)
            return result

        so = self.browse(cr, uid, so_id, context=context)
        if (so and so.sign_date):
            result.update({'result': 'failed', 'err_msg': u'指定编号的订单: %s 已签收!'%sign_info['order_no']})
            _logger.info(result)
            return result

        if (so and so.state in ('draft','sent','cancel')):
            result.update({'result': 'failed', 'err_msg': u'指定编号的订单状态未审核!'})
            _logger.info(result)
            return result

        sign_date = sign_info.get('sign_date', fields.Datetime.now())
        sign_date = datetime.datetime.strptime(sign_date,"%Y/%m/%d %H:%M:%S")
        sign_date = sign_date - datetime.timedelta(hours=8)

        self.write(cr, uid, [so_id], {'sign_date': '%s'%sign_date}, context=context)
        result.update({'result': 'success', 'err_msg': ''})
        self.customer_sign(cr, uid, [so_id], context=context)
        return result

    def sync_buyer_sign(self, cr, uid, sign_info, context=None):
        order = {
            'order_no': '201603301753100124-1',
            'sign_date': '2016-01-01 10:00:00',
        }
        result = self.buyer_sign(cr, uid, order, context=context)
        _logger.info(result)
        return result

    def create_order(self, cr, uid, order, context=None):
        """
        网站接口: 创建订单
        """
        result = {}
        context = context or {}
        partner_obj = self.pool.get('res.partner')
        _logger.info(order)

        #order = json.loads(order)
        #数据检验
        if order.get('order_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少子订单编号参数!'})
            _logger.info(result)
            return result
        if order.get('buyer_nick', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少买家登录名参数!'})
            _logger.info(result)
            return result
        if order.get('payment', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少买家实付款参数!'})
            _logger.info(result)
            return result
        if order.get('total_fee', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少订单总费用参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_name', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人姓名参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_country', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人国籍参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_state', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人所在省份参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_city', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人所在城市参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_district', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人所在地区参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_town', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人街道地址参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_address', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人详细地址参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_zip', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人邮编参数!'})
            _logger.info(result)
            return result
        if order.get('receiver_mobile', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少收货人手机号码参数!'})
            _logger.info(result)
            return result
        if order.get('created', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少交易创建时间参数!'})
            _logger.info(result)
            return result
        if order.get('pay_time', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少付款时间参数!'})
            _logger.info(result)
            return result
        if order.get('modified', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少交易修改时间参数!'})
            _logger.info(result)
            return result
        if order.get('discount_fee', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少优惠减款参数!'})
            _logger.info(result)
            return result
        if order.get('post_fee', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少邮费参数!'})
            _logger.info(result)
            return result
        if order.get('order_lines', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少订单明细参数!'})
            _logger.info(result)
            return result
        if order.get('payment_lines', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少付款参数!'})
            _logger.info(result)
            return result

        so_ids = self.search(cr, uid, [('name', '=', order['order_no'])], context=context)
        so_id = len(so_ids) and so_ids[0] or False
        if so_id:
            result.update({'result': 'failed', 'err_msg': u'指定编号的订单已存在: %s!' % order['order_no']})
            _logger.info(result)
            return result


        partner_id = partner_obj.find_or_create_partner(cr, uid, order, context=context)
        delivery_addr_id = partner_obj.find_or_create_delivery_addr(cr, uid, order, partner_id, context=context)
        invoice_addr_id = False
        if order.get('is_invoice'):
            invoice_addr_id = partner_obj.find_or_create_invoice_addr(cr, uid, order, partner_id, context=context)

        order_vals = self._prepare_order(cr, uid, order, partner_id, delivery_addr_id, invoice_addr_id, context=context)
        pricelist_id = order_vals['pricelist_id']
        order_vals.setdefault('order_line', [])
        for line in order.get('order_lines'):
            line_vals = self._prepare_website_order_line(cr, uid, line, partner_id, pricelist_id, context=context)
            if line_vals.get('result', 'success') == 'success':
                if (not order_vals.get('warehouse_id')):
                    product_obj = self.pool.get('product.product')
                    product_obj = product_obj.browse(cr, uid, [line_vals['product_id']], context=context)
                    if product_obj.product_tmpl_id.seller_id:
                        order_vals.update({'warehouse_id': product_obj.product_tmpl_id.seller_id.stock_warehouse_id.id})
                    else:
                        result.update({'result': 'failed', 'err_msg': u'产品 [%s] 没有供应商!' % line_vals['name']})
                        _logger.info(result)
                        return result
                order_vals.get('order_line').append((0, False, line_vals))
            else:
                return  line_vals

        # 优惠减款
        if order.get('discount_fee'):
            discount_line_vals = self._prepare_discount_order_line(cr, uid, order.get('discount_fee', None), partner_id, pricelist_id, context=context)
            if discount_line_vals.get('result', 'success') == 'success':
                order_vals.get('order_line').append((0, False, discount_line_vals))
            else:
                return discount_line_vals

        # 配送费
        if order.get('post_fee'):
            post_line_vals = self._prepare_post_order_line(cr, uid, order.get('post_fee'), partner_id, pricelist_id, context=context)
            if post_line_vals.get('result', 'success') == 'success':
                order_vals.get('order_line').append((0, False, post_line_vals))
            else:
                return post_line_vals

        # 支付明细
        order_vals.setdefault('payment_lines', [])
        for pay_line in order.get('payment_lines', []):
            pay_line_vals = self._prepare_payment_line(cr, uid, pay_line, context=context)
            if pay_line_vals.get('result', 'success') == 'success':
                pay_line_vals.update({'pay_time': order_vals['date_order']})
                order_vals.get('payment_lines').append((0, False, pay_line_vals))
            else:
                return pay_line_vals

        order_id = self.create(cr, uid, order_vals, context=context)

        #由客服人工审核
        #self.action_button_confirm(cr, uid, [order_id], context=context)

        # 创建发票
        # self.manual_invoice(cr, uid, [order_id], context=context)
        result.update({'result':'success','err_msg':''})
        return result

    def sync_order_from_shop(self, cr, uid, order, context=None):
        # order = {
        #     'order_no': 'SC1133113131113',
        #     'parent_order_no': 'PON00000131',
        #     'buyer_nick': 'hefeilaowang',
        #     'buyer_ID': '340103197810304052',
        #     'payment': 10.0,
        #     'total_fee': 10.0,
        #     'receiver_country': '中国',
        #     'receiver_state': '上海市',
        #     'receiver_city': '上海市',
        #     'receiver_district': '徐汇区',
        #     'receiver_town': '街道地址',
        #     'receiver_address': '五洲大厦801',
        #     'receiver_zip': '230001',
        #     'receiver_mobile': '13333333333',
        #     'receiver_phone': '020-12345678',
        #     'created': '2015-01-01 10:00:00',
        #     'pay_time': '2015-01-01 10:04:34',
        #     'modified': '2015-01-01 10:01:31',
        #     'buyer_memo': 'afsdfdsf',
        #     'is_invoice': False,
        #     'discount_fee': 0,
        #     'post_fee': 0,
        #     'order_lines':[
        #         {
        #             'price': 19.9,
        #             'product_code': '62508de6-f628-11e5-9f44-00163e003060',
        #             'subtotal': 19.9,
        #             'amount': 1
        #         },
        #         {
        #             'price': 19.9,
        #             'product_code': '6241688e-f628-11e5-9f44-00163e003060',
        #             'subtotal': 19.9,
        #             'amount': 1
        #         }
        #     ],
        #     'payment_lines':[
        #         {
        #             'payment_method': 'alipay',
        #             'payment_no': 'PAY111331',
        #             'amount': 10.0,
        #         },
        #     ],
        #     'receiver_name': 'jswang',
        # }
        order = {'order_no': '201604211523490473-a3',
                 'pay_time': '2016/4/21 15:24:02',
                 'receiver_town': u'京九北路佰昌武汉北电商批发城',
                 'receiver_address': u'京九北路佰昌武汉北电商批发城',
                 'receiver_country': u'中国',
                 'order_lines': [{'price': 9.3,
                                  'product_code': '100525',
                                  'subtotal': 9.3,
                                  'amount': 1}],
                 'receiver_district': u'新　县',
                 'receiver_city': u'信阳市',
                 'payment_lines': [{'payment_method': 'appwxpay',
                                    'payment_no': '4009482001201604215058441708',
                                    'amount': 9.3}],
                 'buyer_memo': u'',
                 'post_fee': 8.0,
                 'discount_mode': u' 注册有礼----注册得8元红包券 ',
                 'parent_order_no': '201604211523490473',
                 'receiver_phone': '13303979921',
                 'receiver_zip': '000000',
                 'receiver_mobile': '13303979921',
                 'is_selfsupport': True,
                 'payment': 9.3,
                 'created': '2016/4/21 15:23:49',
                 'discount_fee': -8.0,
                 'is_invoice': False,
                 'buyer_nick': '13303979921',
                 'modified': '2016/4/21 15:23:49',
                 'end_time': '2016/4/21 15:23:49',
                 'total_fee': 17.3,
                 'receiver_state': u'河南省',
                 'invoice_name': u'',
                 'receiver_name': u'张飞',
                 'buyer_ID': u''}
        result = self.create_order(cr, uid, order, context=context)
        _logger.info(result)
        return result

    def sync_payment_lines(self, cr, uid, order, context=None):
        payment_lines = {}
        order_name = order.get('order_no')
        result = {}
        order_id = self.search(cr, uid, [('name','=',order_name)])
        if not order_id:
            result.update({'result':'failed','err_msg':u'没找到对应的销售订单%s!'%order_name})
            _logger.info(result)
            return result
        payment_lines.setdefault('payment_lines', [])
        for pay_line in order.get('payment_lines',[]):
            pay_line_vals = self._prepare_payment_line(cr, uid, pay_line, context=context)
            if pay_line_vals.get('result', 'success') == 'success':
                pay_line_vals.update({'pay_time': order.get('pay_time')})
                payment_lines.get('payment_lines').append((0, False, pay_line_vals))
            else:
                return payment_lines
        self.write(cr, uid, order_id[0], payment_lines, context=context)
        result.update({'result':'success','err_msg':''})
        return result

    def _prepare_order(self, cr, uid, order, partner_id, delivery_addr_id, invoice_addr_id, context=None):
        vals = self.onchange_partner_id(cr, uid, [], partner_id, context=context)['value']

        pay_time = order.get('pay_time', fields.Datetime.now())
        pay_time = datetime.datetime.strptime(pay_time,"%Y/%m/%d %H:%M:%S")
        pay_time = pay_time - datetime.timedelta(hours=8)
        created = datetime.datetime.strptime(order.get('created', fields.Datetime.now()),"%Y/%m/%d %H:%M:%S")
        created = created - datetime.timedelta(hours=8)

        vals.update({
            'name': order['order_no'],
            'date_order': pay_time,  # 订单支付时间
            'create_date': created,  # 订单创建时间
            'partner_id': partner_id,
            'partner_shipping_id': delivery_addr_id,
            # 'warehouse_id': shop.warehouse_id.id,
            'is_cod':order.get('is_cod',False),
            'note': order.get('buyer_memo'),
            #'code': order.get('buyer_ID'),
            # 'seller_memo': trade.get('seller_memo'),
            'delivery_date': order.get('delivery_date'),
            'delivery_hour': order.get('delivery_hour'),
            'picking_policy': 'one',
            'fapiao': order.get('is_invoice'),
            'fp_text': order.get('invoice_name'),
            'order_policy': 'manual',
            'order_line': [],
        })
        if invoice_addr_id:
            vals['partner_invoice_id'] = invoice_addr_id

        return vals

    def _make_order_line(self, cr, uid, prod_id, price_unit, qty, partner_id, pricelist_id, context):
        line_obj = self.pool.get('sale.order.line')
        product_obj = self.pool.get('product.product')
        prod = product_obj.browse(cr, uid, prod_id, context=context)

        line_vals = line_obj.product_id_change(cr, uid, [], pricelist_id, prod_id, qty=qty, partner_id=partner_id, context=context)['value']
        tax_id = line_vals.get('tax_id')
        line_vals.update({
            'product_id': prod.id,
            'price_unit': price_unit,
            'product_uom_qty': qty,
            'tax_id': tax_id and [(6, 0, tax_id)]
        })
        # _logger.info("======================line_vals")
        # _logger.info(line_vals)

        return line_vals

    def _prepare_website_order_line(self, cr, uid, line, partner_id, pricelist_id, context=None):
        """
        网站的订单行
        """
        result = {}
        if line.get('product_code', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少产品编码参数!'})
            _logger.info(result)
            return result
        if line.get('price', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少单价参数!'})
            _logger.info(result)
            return result
        if line.get('amount', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少数量参数!'})
            _logger.info(result)
            return result
        if line.get('subtotal', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少实付款参数!'})
            _logger.info(result)
            return result

        product_obj = self.pool.get('product.product')
        product_code = line['product_code']
        prod_ids = product_obj.search(cr, uid, [('guid', '=', product_code)], context=context)
        # _logger.info(prod_ids)
        # _logger.info(product_code + "===================================GUID")
        if not prod_ids:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编码的产品%s!' % product_code})
            _logger.info(result)
            return result

        return self._make_order_line(cr, uid, prod_ids[0], line['price'], line['amount'], partner_id, pricelist_id, context=context)

    def _prepare_discount_order_line(self, cr, uid, discount_fee, partner_id, pricelist_id, context=None):
        """
        创建优惠减款订单行
        """
        dataobj = self.pool.get('ir.model.data')
        dis_prod_id = dataobj.xmlid_to_res_id(cr, uid, 'bysun_stock_product.ebiz_shop_product_yhjk')
        return self._make_order_line(cr, uid, dis_prod_id, discount_fee, 1, partner_id, pricelist_id, context=context)

    def _prepare_post_order_line(self, cr, uid, post_fee, partner_id, pricelist_id, context=None):
        """
        创建邮费订单行
        """
        dataobj = self.pool.get('ir.model.data')
        dis_prod_id = dataobj.xmlid_to_res_id(cr, uid, 'bysun_stock_product.ebiz_shop_product_yf')
        return self._make_order_line(cr, uid, dis_prod_id, post_fee, 1, partner_id, pricelist_id, context=context)

    def _prepare_payment_line(self, cr, uid, pay_line, context=None):

        result = {}
        if pay_line.get('payment_method', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少支付方式编码参数!'})
            _logger.info(result)
            return result
        if pay_line.get('payment_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少支付流水号参数!'})
            _logger.info(result)
            return result
        if pay_line.get('amount', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少支付金额参数!'})
            _logger.info(result)
            return result

        journal_obj = self.pool.get('account.journal')
        journal_ids = journal_obj.search(cr, uid, [('website_code', '=', pay_line.get('payment_method'))], context=context)
        journal_id = journal_ids and journal_ids[0] or False
        if not journal_id:
            result.update({'result': 'failed' ,'err_msg': u'找不到指定的付款分类账%s!'%pay_line.get('payment_method')})
            _logger.info(result)
            return result
        #    raise exceptions.MissingError(u'找不到指定的付款分类账: %s' % pay_line.get('payment_method'))
        vals = {
            'journal_id': journal_id,
            'ref': pay_line['payment_no'],
            'amount': float(pay_line['amount']),
        }
        return vals

    def cancel_order(self, cr, uid, obj, context=None):
        """取消订单"""
        order_no = obj.get('order_no', False)
        res = {}
        if not order_no:
            res.update(result='3', err_msg=u'订单号为空!')
            return res

        ids = self.search(cr, uid, [('name', '=', order_no)], context=context)
        if not ids:
            res.update(result='2', err_msg=u'订单不存在!')
            return res

        order = self.browse(cr, uid, ids[0], context=context)
        res = {}
        if order.shipped:
            res.update(result='1', err_msg=u'订单已出库,不允许取消')
            return res

        if order.state == 'cancel':
            res.update(result='1', err_msg=u'订单已取消,不允许取消')
            return res

        self.action_cancel(cr, uid, [order.id], context=context)
        res.update(result='0')
        return res

    def change_so_pause(self, cr, uid, obj, context=None):
        """挂起解挂订单 """
        order_no = obj.get('order_no', False)
        _logger.info(obj)
        res = {}
        if not order_no:
            res.update(result='4', err_msg=u'订单号为空!')
            return res

        ids = self.search(cr, uid, [('name', '=', order_no)], context=context)
        if not ids:
            res.update(result='3', err_msg=u'订单不存在!')
            return res

        order = self.browse(cr, uid, ids[0], context=context)
        if order.state == 'cancel':
            res.update(result='2', err_msg=u'订单已取消,不允许挂起')
            return res

        if order.shipped:
            res.update(result='1', err_msg=u'订单已出库,不允许挂起')
            return res

        self.action_suspend(cr, uid, [order.id], context=context)
        res.update(result='0')
        return res
