# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging
import hashlib

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = 'res.partner'

    digest = fields.Char(u'Digest', size=16, index=True)
    receiver_lat = fields.Float(u'纬度',digits=(12,7))
    receiver_lng = fields.Float(u'经度',digits=(12,7))
    code = fields.Char(u'编码')

    def find_or_create_partner(self, cr, uid, order, context=None):
        partner_name = order['buyer_nick']
        ID_Card = order.get('buyer_ID','')
        partner_ids = self.search(cr, uid, [('name', '=', partner_name), ('is_company', '=', True), ('code', '=', ID_Card)], context=context)
        partner_id = len(partner_ids) and partner_ids[0] or False
        if not partner_id:
            country_ids = self.pool.get('res.country').search(cr, uid, [('code', '=', 'CN')], context=context)
            partner_val = {
                'name': partner_name,
                'is_company': True,
                'customer': True,
                'supplier': False,
                'country_id': country_ids and country_ids[0],
                'code': ID_Card,
            }
            _logger.info(partner_val)
            partner_id = self.create(cr, uid, partner_val, context=context)
        return partner_id

    def find_or_create_addr(self, cr, uid, order, addr_type, partner_id, context=None):
        """"根据订单中的地址参数，寻找是否存在该地址, 不存在则创建"""
        addr_digest = self._addr_digest(cr, uid, order, context=context)
        addr_ids = self.search(cr, uid, [('digest', '=', addr_digest), ('type', '=', addr_type)], context=context)
        addr_id = addr_ids and addr_ids[0] or False
        if not addr_id:
            country_id = self.pool.get('res.country').search(cr, uid, [('code', '=', 'CN')], context=context)
            state_id = country_id and self.pool.get('res.country.state').search(cr, uid, [('name', '=', order.get('receiver_state')), ('country_id', '=', country_id[0])], context=context)
            addr_val = {
                'parent_id': partner_id,
                'name': order.get('receiver_name'),
                'phone': order.get('receiver_phone'),
                'mobile': order.get('receiver_mobile'),
                'country_id': country_id and country_id[0] ,
                'state_id': state_id and state_id[0],
                'city': order.get('receiver_city'),
                'street2': order.get('receiver_district'),
                'street': order.get('receiver_address'),
                'type': addr_type,
                'receiver_lat':order.get('receiver_lat'),
                'receiver_lng':order.get('receiver_lng'),
                'digest': addr_digest,
                'use_parent_address': False,
                'is_company': False,
                'customer': False,
                'supplier': False,
            }
            addr_id = self.create(cr, uid, addr_val, context = context)

        return addr_id

    def find_or_create_delivery_addr(self, cr, uid, order, partner_id, context=None):
        """"根据订单中的地址参数，寻找是否存在该地址, 不存在则创建"""

        delivery_addr_id = self.find_or_create_addr(cr, uid, order, 'delivery', partner_id, context=context)
        return delivery_addr_id

    def find_or_create_invoice_addr(self, cr, uid, order, partner_id, context=None):
        """"根据订单中的地址参数，寻找是否存在该地址, 不存在则创建"""
        invoice_addr_id = self.find_or_create_addr(cr, uid, {'buyer_nick': order.get('invoice_name')}, 'invoice', partner_id, context=context)
        return invoice_addr_id

    def _addr_digest(self, cr, uid, order, context=None):
        partner_name = order['buyer_nick']
        keys = self.format_addr_fields(order)
        vals = [partner_name] + [order[k] for k in keys]
        addr_digest = ":".join(vals)
        if isinstance(addr_digest, unicode):
            addr_digest = addr_digest.encode('utf8')
        addr_digest = hashlib.md5(addr_digest).hexdigest()
        return addr_digest

    @staticmethod
    def format_addr_fields(order):
        keys = ["receiver_name", "receiver_phone", "receiver_mobile", "receiver_state", "receiver_city", "receiver_district", "receiver_address", ]
        for k in keys:
            order[k] = (order.get(k, False) or '').strip()
        return keys
