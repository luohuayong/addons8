# -*- encoding: utf-8 -*-

import logging
from openerp.osv import fields, osv, expression
from openerp import tools, exceptions

class ebiz_supplier_account_line(osv.osv):
    _inherit = ['ebiz.supplier.account.line']

    def create(self, cr, uid, vals, context=None):
        product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gyskk')
        if product_id:
            if context is None:
                context = {}
            product_id = product_id[1]
            if context.get('default_product_id', False) == product_id:
                if vals.get('standard_price') * vals.get('amount') >= 0 or vals.get('amount') >= 0:
                    raise exceptions.ValidationError(u'数量必须为负数，且单价乘以数量必须为负数！')
                customer_complain = self.pool.get('ebiz.customer.complain')
                if context.get('default_origin',False):
                    complain_ids = customer_complain.search(cr, uid, [('name','=',context.get('default_origin',False))], context=context)
                    customer_complain.write(cr, uid, complain_ids, {'expense_exists': True})
        return super(ebiz_supplier_account_line, self).create(cr, uid, vals, context)

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        result = super(ebiz_supplier_account_line, self).onchange_product_id(cr, uid, ids, product_id, context=context)
        gyskk = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gyskk')
        gyskk_id = gyskk and gyskk[1] or False
        if gyskk_id == product_id:
            result['value'].update({'amount': -1})
        return result
