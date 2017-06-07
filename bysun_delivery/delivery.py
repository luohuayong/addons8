# -*- encoding: utf-8 -*-\
import logging
from openerp import tools, api, exceptions
from openerp.osv import fields,osv
from lxml import etree as ET
import requests
import urllib
import base64
import hashlib
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class ebiz_shop(osv.osv):
    _inherit = 'ebiz.shop'

    _columns = {
        'yt_url':fields.char(u'圆通接口地址'),
        'clientid':fields.char(u'圆通账号'),
        'yt_pwd':fields.char(u'圆通密钥'),
        'order_type':fields.char(u'圆通快递订单类型'),
        'servicetype':fields.char(u'圆通服务类型'),
    }

    _defaults = {
        'order_type':'1',
        'servicetype':'0',
    }

    def remote_logistics_call(self, cr, uid, vals, context=None):
        shops = self.search(cr, uid, [])
        shop = shops and shops[0] or False
        if not shops:
            raise exceptions.MissingError(u'没有定义电商店铺')
        shop = self.browse(cr, uid, shop)
        http_url = shop.yt_url or False
        if not http_url:
            raise exceptions.MissingError(u'没有定义圆通接口地址')
        result = {}
        try:
            read = requests.post(http_url, data=vals)
            _logger.info(read)
            _logger.info(read.content)
            res_xml = ET.XML(read.content)
            res = res_xml.find('success').text
            if res == 'true':
                distributeInfo = res_xml.find('distributeInfo')
                shortAddress = distributeInfo.find('shortAddress')
                if shortAddress is not None:
                    mailNo = res_xml.find('mailNo')
                    result.update({'result':'success','err_msg':'','mailNo':mailNo.text,'shortAddress':shortAddress.text})
                else:
                    result.update({'result':'fail','err_msg':u'不能解析的错误地址'})
            else:
                reason = res_xml.find('reason')
                if reason is not None:
                    reason = res_xml.find('reason').text
                else:
                    reason = ''
                result.update({'result':'fail','err_msg':reason})
        except Exception,e:
            result.update({'result':'fail','err_msg':u'网络错误或者圆通地址配置错误'})
        _logger.info(result)
        return result

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def customer_sign(self, cr, uid, ids, context=None):
        res = super(sale_order, self).customer_sign(cr, uid, ids, context=context)
        picking_id = context and context.get('picking_id')
        if picking_id:
            sale_logistic = self.pool['sale.order.logistic']
            sl_vals = {'name': 'signed', 'user_id': uid, 'order_id': ids[0], 'state': 'draft', 'memo':u'客户签收'}
            sale_logistic.create(cr, uid, sl_vals, context=context)

            picking_obj = self.pool.get('stock.picking')
            picking_obj.write(cr, uid, [picking_id], {'customer_signed': True}, context=context)

        return res


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'customer_signed':fields.boolean(u'客户签收'),
        'sanduan_code':fields.char(u'圆通三段码'),
    }

    def is_ec_order(self, cr, uid, id, context=None):
        group_id = self.read(cr, uid, id, ['group_id'], context=context)['group_id']
        so = group_id and group_id[1]
        if not so: return False
        if so and so.startswith('SO'):
            return False
        return True

    def search_by_package(self, cr, uid, package_ref, context=None):
        pack_model = self.pool['stock.quant.package']
        operation_model = self.pool['stock.pack.operation']
        picking_ids = self.search(cr, uid, [('carrier_tracking_ref', '=', package_ref), ('state', 'not in', ['cancel', 'done']),('picking_type_code','=','outgoing')], context=context)
        if not picking_ids:
            res = operation_model.search_read(cr, uid, [('result_package_id.name', '=', package_ref)], ['picking_id'], context=context)
            if res:
                picking_id = res[0]['picking_id']
                if picking_id:
                    group_id = self.read(cr, uid, picking_id[0], ['group_id'], context=context)['group_id']
                    if group_id:
                        picking_ids = self.search(cr, uid, [('group_id', '=', group_id[0]), ('state', 'not in', ['cancel', 'done'])], context=context)
        
        return picking_ids

    def prepare_post_vals(self, cr, uid, RequestOrder, shop, context=None):
        m = hashlib.md5()
        val = RequestOrder + shop.yt_pwd
        m.update(val)
        val = m.digest()
        val = base64.b64encode(val)
        val = urllib.quote(val)

        vals = {
            'clientId':shop.clientid,
            'logistics_interface':RequestOrder,
            'data_digest':val,
        }
        return vals

    def prepare_logistics_interface_order(self, cr, uid, ids, context=None):
        ebiz_shop = self.pool['ebiz.shop']
        shops = ebiz_shop.search(cr, uid, [])
        shop = shops and shops[0] or False
        if not shops:
            raise exceptions.MissingError(u'没有定义电商店铺')
        shop = ebiz_shop.browse(cr, uid, shop)
        if not (shop.clientid and shop.yt_pwd):
            raise exceptions.MissingError(u'没有定义圆通账号或密钥')
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
            raise exceptions.ValidationError(err_msg)
        requese_xml_dict = {}
        for right_picking in pickings:
            RequestOrder = ET.Element('RequestOrder')
            clientID = ET.Element('clientID')
            clientID.text = shop.clientid # 需要设置为可配置
            logisticProviderID = ET.Element('logisticProviderID')
            logisticProviderID.text = 'YTO'
            # 获取订单单号
            txLogisticID = ET.Element('txLogisticID')
            txLogisticID.text = right_picking.sale_id.name
            # 设置收件人信息
            receiver = ET.Element('receiver')
            r_name = ET.Element('name')
            r_name.text = right_picking.sale_id.partner_shipping_id.name
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

            # 设置发件人信息
            sender = ET.Element('sender')
            s_name = ET.Element('name')
            s_name.text = shop.warehouse_id.partner_id.name
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

            # 商品信息
            items = ET.Element('items')
            # 做循环获取商品信息
            for move in right_picking.move_lines:
                item = ET.Element('item')
                itemName = ET.Element('itemName')
                itemName.text = move.product_id.name
                number = ET.Element('number')
                number.text = str(int(move.product_uom_qty))
                item.append(itemName)
                item.append(number)

            # 循环完毕
            items.append(item)

            customerId = ET.Element('customerId')
            customerId.text = shop.clientid
            orderType = ET.Element('orderType')
            orderType.text = shop.order_type # 需要设置为可配置
            serviceType = ET.Element('serviceType')
            serviceType.text = shop.servicetype # 需要设置为可配置

            RequestOrder.append(items)
            RequestOrder.append(logisticProviderID)
            RequestOrder.append(clientID)
            RequestOrder.append(sender)
            RequestOrder.append(receiver)
            RequestOrder.append(orderType)
            RequestOrder.append(txLogisticID)
            RequestOrder.append(customerId)
            RequestOrder = ET.tostring(RequestOrder)
            post_val = self.prepare_post_vals(cr, uid, RequestOrder, shop, context=context)
            requese_xml_dict.update({right_picking.id:post_val})
        return requese_xml_dict

    def open_customer_sign(self, cr, uid, ids, context=None):
        context = dict(context or {})
        pid = ids and ids[0]
        if not pid:
            raise exceptions.MissingError(u'未找到拣货单!')

        picking = self.browse(cr, uid, pid, context=context)
        if not picking.sale_id:
            raise exceptions.MissingError(u'未找到关联的销售订单!')

        if picking.picking_type_code != 'outgoing':
            raise exceptions.ValidationError(u'非出库单,不能签收!')

        so_obj = self.pool.get('sale.order')
        sale_id = picking.sale_id.id
        context.update({
            'picking_id': picking.id,
            'active_id': sale_id,
            'active_ids': [sale_id],
        })
        res = so_obj.prepare_customer_sign(cr, uid, [sale_id], context=context)
        return res

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    def _prepare_picking_assign(self, cr, uid, move, context=None):
        """ 多步出库时候，由Procurement Order产生Stock Picking时候，从SO上取得配送日期、配送时段，
             填入新产生的Picking
        """
        values = super(stock_move, self)._prepare_picking_assign(cr, uid, move, context=context)
        if move.group_id:
            so_ids = self.pool['sale.order'].search(cr, uid, [('name', '=', move.group_id.name)], context=context)
            if so_ids:
                so = self.pool['sale.order'].read(cr, uid, so_ids[0], ['delivery_date', 'delivery_hour'], context=context)
                print so
                values.update({'delivery_hour': so.get('delivery_hour',''), 'delivery_date': so.get('delivery_date',False) })
        return values

class stock_picking_wave(osv.osv):
    _inherit = 'stock.picking.wave'

    _columns = {
        'error_order':fields.char(u'无法识别条码'),
        'carrier_id':fields.many2one('delivery.carrier', u'快递公司'),
    }

    def print_delivery_wave(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        picking_ids = self.pool['stock.picking'].search(cr, uid, [('wave_id','in',ids)])
        if not picking_ids:return True
        return {
            'type' : 'ir.actions.report.xml',
            'report_type':'qweb-pdf',
            'report_name':'bysun_delivery.oscg_delivery_order',
            'data':picking_ids,
        }

    def confirm_picking(self, cr, uid, ids, context=None):
        picking_todo = self.pool.get('stock.picking').search(cr, uid, [('wave_id', 'in', ids),('state','!=','assigned')], context=context)
        self.write(cr, uid, ids, {'state': 'in_progress'}, context=context)
        return self.pool.get('stock.picking').action_assign(cr, uid, picking_todo, context=context)

    def done(self, cr, uid, ids, context=None):
        picking_todo = set()
        transfer_model = self.pool['stock.transfer_details']
        for wave in self.browse(cr, uid, ids, context=context):
            for picking in wave.picking_ids:
                if picking.state in ('cancel', 'done'):
                    continue
                if picking.state not in ['assigned' ,'partially_available']:
                    raise osv.except_osv(_('Warning'), _('Some pickings are still waiting for goods. Please check or force their availability before setting this wave to done.'))
                picking_todo.add(picking.id)
        if picking_todo:
            for picking in picking_todo:
                ctx = context.copy()
                ctx.update({'active_id':picking,'active_model':'stock.picking','active_ids':[picking]})
                created_id = transfer_model.create(cr, uid, {'picking_id': picking or False}, ctx)
                transfer_model.do_detailed_transfer(cr, uid, created_id, context=ctx)
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)

class delivery_vehicle(osv.osv):
    _name = 'delivery.vehicle'

    _columns = {
        'name':fields.char(u'车牌号'),
        'description':fields.char(u'说明'),
    }

class delivery_driver(osv.osv):
    _name = 'delivery.driver'

    _columns = {
        'name':fields.char(u'姓名'),
        'description':fields.char(u'说明'),
    }

class delivery_schedule(osv.osv):
    _name = 'delivery.schedule'

    _columns = {
        'name':fields.date(u'名称'),
        'delivery_id':fields.many2one('delivery.carrier',u'运输方式'),
        'vehicle':fields.many2one('delivery.vehicle', u'车牌'),
        'driver':fields.many2one('delivery.driver', u'司机'),
    }

class delivery_carrier(osv.osv):
    _inherit = 'delivery.carrier'
    _columns = {
        'association_method': fields.selection([('general_rule',u'加1规则'),('six_four_rule',u'逢6加4递增11'),('daily_rule',u'天天规则'),('ems_rule',u'EMS快递单号'),('shunfeng_rule',u'顺丰规则')],u'面单联号规则'),
        'report_id': fields.many2one('ir.actions.report.xml', u'面单格式'),
        'next_sequence':fields.char(u'下次打印序列号'),
    }

    _defaults = {
        'next_sequence':'0',
    }

    def _next_seq(self, association_method, first_seq, context=None):
        res_seq = False
        if association_method == 'general_rule':
            if len(first_seq) <= 6:
                raise osv.except_osv('Warning !', u'初始订单号应大于6位！')
            i = len(first_seq)-1
            while first_seq[i] in ['0','9'] and i > 0:
                i = i - 1
            order_start = first_seq[0:i]
            order_end = int(first_seq[i:])+1
            res_seq = order_start+str(order_end)
        elif association_method == 'six_four_rule':
            if len(first_seq) != 12:
                raise osv.except_osv('Warning !', u'初始订单号应为12位！')
            order = int(first_seq)
            order_end = int(first_seq[-1])
            seq = 0
            if order_end == 6:
                seq = order+4
            else:
                seq = order+11
            res_seq = str(seq)
        elif association_method == 'daily_rule':
            if len(start_carrier_order) < 12:
                raise osv.except_osv('Warning !', u'初始订单号应大于12位！')
            order1_abs = int(first_seq[-1])
            if order1_abs < 3:
                order1_abs = (order1_abs+10)-3
            else:
                order1_abs = order1_abs-3
            order_before3 = int(first_seq[:-1])+1
            res_seq = str(order_before3)+str(order1_abs)
        elif association_method == 'ems_rule':
            if len(start_carrier_order) != 13:
                raise osv.except_osv('Warning !', u'初始订单号应为13位！')
            order_before = first_seq[:2]
            order_end = first_seq[-2:]
            order_mid8 = str(int(first_seq[2:-3])+1)
            if len(order_mid8) != 8:
                order_mid8 = '0'*(8-len(order_mid8))+order_mid8
            list_mid = [int(vl) for vl in order_mid8]
            mod = (8*list_mid[0]+6*list_mid[1]+4*list_mid[2]+2*list_mid[3]+3*list_mid[4]+5*list_mid[5]+9*list_mid[6]+7*list_mid[7])%11
            value = 11- mod
            if mod == 0:
                value =5
            elif mod == 1:
                value = 0
            else:
                value = value
            res_seq = order_before+order_mid8+str(value)+order_end
        elif association_method == 'shunfeng_rule':
            if len(first_seq) != 12:
                raise osv.except_osv('Warning !', u'初始订单号应为12位！')
            #顺丰单号连打规则
            # 单号最后四位，记着 s[0]、s[1]、s[2]、s[3]
            #1) 如果s[1]、s[2]都是9，如果s[0]是偶数，加12，如果s[0]是奇数，加13，得到下一单号
            #2) 如果s[2]是9，s[1]是[0,1,2,4,5,7,8]之一，加16，s[1]是[3,6]之一，加15，得到下一单号
            #3) 其他情况，直接加9得到下一单号
            order_end = first_seq[-4:]
            if order_end[1]=='9' and order_end[2]=='9':
                if int(order_end[0])%2 == 0:
                    res_seq = int(order_end) + 13
                else:
                    res_seq = int(order_end) + 12
            elif order_end[2]=='9':
                if order_end[1] in [0,1,2,4,5,7,8]:
                    res_seq = int(order_end) + 16
                else:
                    res_seq = int(order_end) + 15
            else:
                res_seq = int(order_end) + 9
            res_seq = "%s%s" % (first_seq[0:-4], res_seq)
        return res_seq
        
    def generate_seq(self, cr, uid, id, start, count, end=None,context=None):
        carrier_id = self.browse(cr,uid,id,context=context)
        method = carrier_id.association_method
        if not method:
            raise osv.except_osv('Warning !', u'请确认快递公司【%s】设置了联号规则!' % (carrier_id.name, ) )
        seq_list = [start]
        self._next_seq(method, start)
        prev = start
        if end:
            while prev != end:
                if len(seq_list) < count:
                    next = self._next_seq(method, prev)
                    seq_list.append(next)
                    prev = next
                else:
                    break
        else:
            while len(seq_list) < count:
                next = self._next_seq(method, prev)
                seq_list.append(next)
                prev = next
        return seq_list

delivery_carrier()