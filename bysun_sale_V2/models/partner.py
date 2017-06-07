# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging
import hashlib
import base64

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = 'res.partner'

    digest_new = fields.Char(u'MD5', index=True)

    name = fields.Char('Name', required=True, select=True, track_visibility='always')
    phone = fields.Char('Phone', track_visibility='always')
    mobile = fields.Char('Mobile', track_visibility='always')
    street = fields.Char('Street', track_visibility='always')
    street2 = fields.Char('Street2', track_visibility='always')
    city = fields.Char('City', track_visibility='always')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict', track_visibility='always')

    def find_or_create_addr(self, cr, uid, order, addr_type, partner_id, context=None):
        """"根据订单中的地址参数，寻找是否存在该地址, 不存在则创建"""
        addr_digest = self._addr_digest(cr, uid, order, context=context)
        addr_ids = self.search(cr, uid, [('digest_new', '=', addr_digest), ('type', '=', addr_type)], context=context)
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
                'digest_new': addr_digest,
                'use_parent_address': False,
                'is_company': False,
                'customer': False,
                'supplier': False,
            }
            addr_id = self.create(cr, uid, addr_val, context = context)

        return addr_id


    @api.multi
    def write(self, vals):
        for partner in self:
            if partner.customer or partner.type == 'delivery':
                #vals包含child_ids，且name, state_id, city, street, street2, mobile, phone任一改变， 需要改变child_ids的digest_new字段
                if vals.get('child_ids', False):
                    for line in vals.get('child_ids'):
                        if line[0] == 1:
                            for child in partner.child_ids:
                                if line[1] == child.id:
                                    city = line[2].get('city', False) or child.city
                                    street = line[2].get('street', False) or child.street
                                    street2 = line[2].get('street2', False) or child.street2
                                    name = line[2].get('name', False) or child.name
                                    mobile = line[2].get('mobile', False) or child.mobile
                                    phone = line[2].get('phone', False) or child.phone
                                    state_name = False
                                    if not line[2].get('state_id', False):
                                        state_name = child.state_id.name
                                    else:
                                        state_id = line[2].get('state_id', False)
                                        for state_obj in self.env['res.country.state'].browse(state_id):
                                            state_name = state_obj.name

                                    MD5_key = {
                                        'buyer_nick': name,
                                        'receiver_phone': phone,
                                        'receiver_mobile': mobile,
                                        'receiver_state': state_name,
                                        'receiver_city': city,
                                        'receiver_district': street2,
                                        'receiver_address': street,
                                    }
                                    line[2].update({'digest_new': partner._addr_digest(MD5_key)})
                else:
                    if vals.get('city', False) or vals.get('street', False) or vals.get('street2', False) or\
                            vals.get('name', False) or vals.get('mobile', False) or vals.get('phone', False) or vals.get('state_id', False):
                        city = vals.get('city', False) or partner.city
                        street = vals.get('street', False) or partner.street
                        street2 = vals.get('street2', False) or partner.street2
                        name = vals.get('name', False) or partner.name
                        mobile = vals.get('mobile', False) or partner.mobile
                        phone = vals.get('phone', False) or partner.phone
                        state_name = False
                        if not vals.get('state_id', False):
                            state_name = partner.state_id.name
                        else:
                            state_id = vals.get('state_id', False)
                            for state_obj in self.env['res.country.state'].browse(state_id):
                                state_name = state_obj.name
                        MD5_key = {
                            'buyer_nick': name,
                            'receiver_phone': phone,
                            'receiver_mobile': mobile,
                            'receiver_state': state_name,
                            'receiver_city': city,
                            'receiver_district': street2,
                            'receiver_address': street,
                        }
                        vals.update({'digest_new': partner._addr_digest(MD5_key)})
        return super(res_partner, self).write(vals)