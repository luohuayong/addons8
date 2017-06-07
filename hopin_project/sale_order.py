# -*- coding: utf-8 -*-
from openerp.osv import osv, fields, expression
import logging
import datetime

_logger = logging.getLogger(__name__)
class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'journal_id': fields.related('payment_lines','journal_id', type='many2one', relation='account.journal', string=u'支付方式'),
        'isenough':fields.boolean(default =True,string=u'是否满足库存'),
        'guidlist':fields.char(default='',string=u'库存不足商品sku'),
        'check_reason':fields.text(default='',string=u'待审核原因',readonly=True),
    }

    def _prepare_payment_line(self, cr, uid, pay_line, context=None):
        vals = super(sale_order, self)._prepare_payment_line(cr, uid, pay_line, context=context)

        vals.update({
            'payorderosn': pay_line['payorderosn'],
        })
        return vals

    # V1.01版本新增商品最大退款金额，老方法无法兼容
    def _make_order_line_product(self, cr, uid, prod_id, price_unit, qty, rebateprice, partner_id, pricelist_id, context):
        line_obj = self.pool.get('sale.order.line')
        product_obj = self.pool.get('product.product')
        prod = product_obj.browse(cr, uid, prod_id, context=context)

        line_vals = line_obj.product_id_change(cr, uid, [], pricelist_id, prod_id, qty=qty, partner_id=partner_id, context=context)['value']
        tax_id = line_vals.get('tax_id')
        line_vals.update({
            'product_id': prod.id,
            'price_unit': price_unit,
            'product_uom_qty': qty,
            'rebateprice':rebateprice,
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
        if line.get('rebateprice', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少最大退款金额参数!'})
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
        _logger.info(line['rebateprice'])
        return self._make_order_line_product(cr, uid, prod_ids[0], line['price'], line['amount'], line['rebateprice'], partner_id, pricelist_id, context=context)

    # def confirm_order(self, cr, uid, context=None):
    #     # ids=self.search(cr, uid,['&',('state','=','draft'),('date_order','<','now()')], context=context)
    #     ids=self.search(cr, uid,[('state','=','draft')], context=context)
    #     _logger.info(ids)
    #
    #     for order in self.browse(cr, uid, ids, context=context):
    #         so_id = len(ids) and order.id or False
    #         _logger.info(order)
    #         check_flag = True
    #         flag = True
    #         amountflag = True
    #         guidlist = ''
    #         check_reason = ''
    #
    #         order_line_obj=self.pool.get('sale.order.line')
    #         oids=order_line_obj.search(cr, uid,[('order_id','=',order.id)], context=context)
    #
    #         _logger.info(datetime.datetime.now())
    #         _logger.info(order.date_order)
    #         _logger.info( datetime.datetime.strptime(order.date_order,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=10))
    #
    #         if  datetime.datetime.now() < datetime.datetime.strptime(order.date_order,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=10):
    #             continue
    #
    #         for line in order_line_obj.browse(cr, uid, oids, context=context):
    #             product_obj = self.pool.get('product.product')
    #             _logger.info('-----------------%s',line.product_id.guid)
    #             product_code = line.product_id.guid
    #             prod_ids = product_obj.search(cr, uid, ['&',('guid', '=', product_code),('type','=','product')], context=context)
    #             _logger.info('-------s----------%s',prod_ids)
    #             if prod_ids:
    #                 product_pro=product_obj.browse(cr, uid,prod_ids, context=context)
    #                 sale_available=sum([p.sale_available for p in product_pro.product_variant_ids])
    #
    #                 amount=line.product_uom_qty
    #                 # 秒杀判断  商品数量 大于 等于 1
    #                 if amount>1:
    #                     amountflag=False
    #
    #                 if amount>sale_available:
    #                     flag=False
    #                     guidlist=guidlist+str(product_code)+','
    #
    #         _logger.info('11111111')
    #         if guidlist!='' and not flag:
    #             check_flag=False
    #             guidlist=guidlist[0:len(guidlist)-1]
    #             check_reason='库存不足,商品sku：'+ guidlist+';'
    #             self.write(cr, uid, [so_id], {'isenough': False,'guidlist':guidlist}, context=context)
    #
    #         _logger.info('2222')
    #
    #         if not amountflag:
    #             check_flag=False
    #             check_reason=check_reason+'秒杀商品购买数量大于1'+';'
    #
    #         if order.note:
    #             check_flag=False
    #             check_reason=check_reason+'买家填写了备注'+';'
    #
    #         if order.amount_total >=500 :
    #             check_flag=False
    #             check_reason=check_reason+'订单金额>=500元'+';'
    #         #
    #         if check_flag:
    #             res = self.action_button_confirm(cr, uid, [so_id], context=None)
    #         else:
    #             self.write(cr, uid, [so_id], {'check_reason': check_reason}, context=context)
    #     return True

    def create_order(self, cr, uid, order, context=None):
        result = super(sale_order, self).create_order(cr, uid, order, context=context)
        if result:
            if result.get('result')== 'success':
                order_no=order['order_no']
                so_ids = self.search(cr, uid, [('name', '=', order_no)], context=context)
                so_id = len(so_ids) and so_ids[0] or False
                if not so_id:
                    result['result']='failed'
                    result['err_msg']=u'创建订单失败'
                    return result
                else:
                    #
                    check_flag=True
                    flag=True
                    amountflag=True
                    guidlist=''
                    check_reason=''
                    for line in order.get('order_lines'):
                        product_obj = self.pool.get('product.product')
                        product_code = line['product_code']
                        prod_ids = product_obj.search(cr, uid, [('guid', '=', product_code)], context=context)
                        product_pro=product_obj.browse(cr, uid,prod_ids, context=context)
                        sale_available=sum([p.sale_available for p in product_pro.product_variant_ids])

                        amount=line.get('amount')
                        # 秒杀判断  商品数量 大于 等于 1
                        if amount>1:
                            amountflag=False

                        if amount>sale_available:
                            flag=False
                            guidlist=guidlist+str(product_code)+','

                    if  guidlist!='' and not flag:
                        check_flag=False
                        guidlist=guidlist[0:len(guidlist)-1]
                        check_reason='库存不足,商品sku：'+ guidlist+';'
                        self.write(cr, uid, [so_id], {'isenough': False,'guidlist':guidlist}, context=context)

                    if  not amountflag:
                        check_flag=False
                        check_reason=check_reason+'秒杀商品购买数量大于1'+';'

                    if order.get('buyer_memo'):
                        check_flag=False
                        check_reason=check_reason+'买家填写了备注'+';'

                    if  order.get('payment') >=500 :
                        check_flag=False
                        check_reason=check_reason+'订单金额>=500元'+';'
                    #
                    # if check_flag:
                    #     res=self.action_button_confirm(cr, uid, [so_id], context=None)
                    # else:
                    #     self.write(cr, uid, [so_id], {'check_reason': check_reason}, context=context)
        return result

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    _columns = {
        'rebateprice':fields.float(string=u'最大退款金额'),
    }

class sale_payment_line(osv.osv):
    _inherit = 'sale.payment.line'

    _columns = {
        'payorderosn':fields.char(string=u'火品支付流水号'),
    }