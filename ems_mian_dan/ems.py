# -*- encoding: utf-8 -*-\
import logging
from lxml import etree as ET
import requests
import urllib
import base64
import hashlib
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ems_carrier_tracking_ref(models.Model):
    _name = 'ems.carrier.tracking.ref'
    _description = u'ems面单号'

    number = fields.Char(u'快递单号',default="0")
    sale_id = fields.Many2one('sale.order',u'销售单号',default=False)
    state = fields.Selection([('no_use',u'未使用'),('using',u'使用中'),('used',u'已使用'),('cancel',u'已废弃')],string=u'使用状态',default="no_use")

class ebiz_shop(models.Model):
    _inherit = 'ebiz.shop'
    _description = '电商店铺'

    ems_url = fields.Char(u'EMS接口地址')
    ems_eccompanyid = fields.Char(u'EMS电商标识')
    ems_partnered = fields.Char(u'EMS数字签名',help=u"测试数字签名为：IFQXpswT3Bsg")
    ems_logisticProviderID = fields.Char(u'EMS物流提供方',help=u"默认固定为'POSTB'",default="POSTB")
    ems_orderType = fields.Integer(u'EMS订单类型', help=u"0-COD;1-普通订单;3-退货单(标准接口默认设置为 1)",default=1)
    ems_tradeNo = fields.Char(u'EMS交易号',help=u"默认固定为'252'",default="252")
    ems_servicetype = fields.Integer(u'EMS服务类型', help=u"0-自己联系;1-在线下单（上门揽收;4-限时物流;8-快捷COD;16-快递保障;(标准接口默认设置为 0)",default=0)

    def remote_ems_logistics_call(self, cr, uid, vals, context=None):
        shops = self.search(cr, uid, [])
        shop = shops and shops[0] or False
        if not shops:
            raise ValidationError(u'没有定义电商店铺')
        shop = self.browse(cr, uid, shop)
        http_url = shop.ems_url or False
        if not http_url:
            raise ValidationError(u'没有定义EMS接口地址')
        result = {}
        try:
            read = requests.post(http_url, data=vals)
            _logger.info(read)
            _logger.info(read.content)
            res = read.content
            if res != 'ok':
                res_xml = ET.XML(res)
                success = res_xml.find('responseItems').find('response').find('success')
                if success.text == 'true':
                    result.update({'result':'success','err_msg':''})
                else:
                    reason = res_xml.find('responseItems').find('response').find('reason')
                    result.update({'result':'fail','err_msg':u'错误代码:%s'%reason.text})
            else:
                result.update({'result':'fail','err_msg':u'数字签名检验失败'})
        except Exception,e:
            result.update({'result':'fail','err_msg':u'网络错误或者EMS地址配置错误'})
        _logger.info(result)
        return result

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def prepare_ems_post_vals(self, cr, uid, RequestOrder, shop, context=None):
        m = hashlib.md5()
        val = RequestOrder + shop.ems_partnered
        m.update(val)
        val = m.digest()
        val = base64.b64encode(val)
        # val = urllib.quote(val)

        vals = {
            'ecCompanyId':shop.ems_eccompanyid,
            'logistics_interface':RequestOrder,
            'data_digest':val,
            'msg_type':'ORDERCREATE',
        }
        return vals

    def prepare_ems_logistics_interface_order(self, cr, uid, ids, context=None):
        ebiz_shop = self.pool['ebiz.shop']
        ems_model = self.pool['ems.carrier.tracking.ref']
        shops = ebiz_shop.search(cr, uid, [])
        shop = shops and shops[0] or False
        if not shops:
            raise ValidationError(u'没有定义电商店铺')
        shop = ebiz_shop.browse(cr, uid, shop)
        if not (shop.ems_eccompanyid and shop.ems_partnered and shop.ems_logisticProviderID):
            raise ValidationError(u'没有定义EMS相关配置信息')

        pickings = []
        error_picking = {}
        for picking in self.browse(cr, uid, ids, context=context):
            if not (picking.sale_id and picking.sale_id.partner_shipping_id or False):
                error_picking.update({picking.name:u'没有对应销售订单或者对应销售订单没有发货地址'})
            else:
                pickings.append(picking)
        if error_picking:
            err_msg = ''
            for err in error_picking:
                err_msg += '%s:%s\n'%(err,error_picking.get(err))
            raise ValidationError(err_msg)
        ems_ids = ems_model.search(cr, uid, [('state','=','no_use'),('sale_id','=',False)],limit=len(ids),order='number')
        if len(ems_ids) < len(ids):raise ValidationError(u'没有足够的EMS快递单号')
        requese_xml_dict = {}
        ems_records = ems_model.browse(cr, uid, ems_ids)
        for right_picking in pickings:
            ems_record = ems_records[pickings.index(right_picking)]
            ems_record.write({'state':'using'})
            RequestOrder = ET.Element('RequestOrder')
            ecCompanyId = ET.Element('ecCompanyId')
            ecCompanyId.text =  shop.ems_eccompanyid# 需要设置为可配置
            logisticProviderID = ET.Element('logisticProviderID')
            logisticProviderID.text = shop.ems_logisticProviderID

            tradeNo = ET.Element('tradeNo')
            tradeNo.text = shop.ems_tradeNo

            # 需要设置为自增长
            mailNo = ET.Element('mailNo')
            mailNo.text = ems_record.number

            # 获取订单单号
            txLogisticID = ET.Element('txLogisticID')
            txLogisticID.text = right_picking.sale_id.name

            # 设置收件人信息
            receiver = ET.Element('receiver')
            r_name = ET.Element('name')
            r_name.text = right_picking.sale_id.partner_shipping_id.name
            r_postCode = ET.Element('postCode')
            r_postCode.text = right_picking.sale_id.partner_shipping_id.zip or '0'
            r_prov = ET.Element('prov')
            r_prov.text = right_picking.sale_id.partner_shipping_id.state_id and right_picking.sale_id.partner_shipping_id.state_id.name or ''
            r_mobile = ET.Element('mobile')
            r_mobile.text = right_picking.sale_id.partner_shipping_id.mobile or right_picking.sale_id.partner_shipping_id.phone or ''
            r_city = ET.Element('city')
            r_city.text = right_picking.sale_id.partner_shipping_id.city or ''
            r_address = ET.Element('address')
            r_address.text = (right_picking.sale_id.partner_shipping_id.street2 or '') + (right_picking.sale_id.partner_shipping_id.street or '') or ''
            receiver.append(r_name)
            receiver.append(r_mobile)
            receiver.append(r_prov)
            receiver.append(r_city)
            receiver.append(r_address)
            receiver.append(r_postCode)

            # 设置发件人信息
            sender = ET.Element('sender')
            s_name = ET.Element('name')
            s_name.text = (len(shop.warehouse_id.partner_id.name) > 16) and shop.warehouse_id.partner_id.name[0:16] or shop.warehouse_id.partner_id.name
            s_postCode = ET.Element('postCode')
            s_postCode.text = shop.warehouse_id.partner_id.zip or '0'
            s_prov = ET.Element('prov')
            s_prov.text = shop.warehouse_id.partner_id.state_id and shop.warehouse_id.partner_id.state_id.name or ''
            s_city = ET.Element('city')
            s_city.text = shop.warehouse_id.partner_id.city or ''
            s_mobile = ET.Element('mobile')
            s_mobile.text = shop.warehouse_id.partner_id.mobile or shop.warehouse_id.partner_id.phone or ''
            s_address = ET.Element('address')
            s_address.text = (shop.warehouse_id.partner_id.street2 or '') + (shop.warehouse_id.partner_id.street or '') or ''
            sender.append(s_name)
            sender.append(s_prov)
            sender.append(s_mobile)
            sender.append(s_city)
            sender.append(s_address)
            sender.append(s_postCode)

            # 商品信息
            items = ET.Element('items')
            # 做循环获取商品信息
            goodsValue_num = 0.00
            for move in right_picking.move_lines:
                item = ET.Element('item')
                itemName = ET.Element('itemName')
                itemName.text = move.product_id.name
                number = ET.Element('number')
                number.text = str(int(move.product_uom_qty))
                itemValue = ET.Element('itemValue')
                # special = ET.Element('special')
                itemValue.text = str(int(move.product_id.list_price))
                item.append(itemName)
                item.append(number)
                item.append(itemValue)
                goodsValue_num += move.product_id.list_price * move.product_uom_qty
                # item.append(special)

            # 循环完毕
            items.append(item)

            customerId = ET.Element('customerId')
            customerId.text = '0'
            orderType = ET.Element('orderType')
            orderType.text = str(shop.ems_orderType) # 需要设置为可配置
            serviceType = ET.Element('serviceType')
            serviceType.text = str(shop.ems_servicetype) # 需要设置为可配置
            sendStartTime = ET.Element('sendStartTime')
            sendEndTime = ET.Element('sendEndTime')
            goodsValue = ET.Element('goodsValue')
            goodsValue.text = str(goodsValue_num)

            totalServiceFee = ET.Element('totalServiceFee')
            buyServiceFee = ET.Element('buyServiceFee')
            codSplitFee = ET.Element('codSplitFee')
            remark = ET.Element('remark')
            weight = ET.Element('weight')
            weight.text = str(right_picking.infact_weight or 0.00)

            RequestOrder.append(items)
            RequestOrder.append(logisticProviderID)
            RequestOrder.append(ecCompanyId)
            RequestOrder.append(sender)
            RequestOrder.append(receiver)
            RequestOrder.append(orderType)
            RequestOrder.append(txLogisticID)
            RequestOrder.append(customerId)
            RequestOrder.append(tradeNo)
            RequestOrder.append(mailNo)
            RequestOrder.append(sendStartTime)
            RequestOrder.append(sendEndTime)
            RequestOrder.append(goodsValue)
            RequestOrder.append(weight)
            RequestOrder.append(totalServiceFee)
            RequestOrder.append(buyServiceFee)
            RequestOrder.append(codSplitFee)
            RequestOrder.append(serviceType)
            RequestOrder.append(remark)
            RequestOrder = ET.tostring(RequestOrder)
            post_val = self.prepare_ems_post_vals(cr, uid, RequestOrder, shop, context=context)
            requese_xml_dict.update({right_picking.id:[post_val,ems_record]})
        return requese_xml_dict

