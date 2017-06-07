# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging
import uuid

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    # def on_change_supplier_mode(self, cr, uid, ids, supplier_mode=False, stock_warehouse_id=False, context=None):
    #     if supplier_mode in ['Direct_Procurement','Consign_stock_in']:
    #         wh_obj = self.pool.get('stock.warehouse').browse(cr, uid, stock_warehouse_id, context=context)
    #         if wh_obj:
    #             value = {}
    #             value['default_recipients'] = wh_obj.partner_id.name
    #             value['default_recipients_phone'] = wh_obj.partner_id.phone or wh_obj.partner_id.mobile
    #             value['default_return_goods_address'] = wh_obj.partner_id.state_id.name + wh_obj.partner_id.city + wh_obj.partner_id.street2 + wh_obj.partner_id.street
    #             return {'value': value}

