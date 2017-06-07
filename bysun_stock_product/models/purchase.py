# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.osv import osv
import logging

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                'picking_type_id': False,
                }}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'], context=context)
        supplier = partner.browse(cr, uid, partner_id, context=context)
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
            'payment_term_id': supplier.property_supplier_payment_term.id or False,
            'picking_type_id':supplier.stock_warehouse_id and supplier.stock_warehouse_id.in_type_id.id or False,
            }}