# -*- coding: utf-8 -*-
from openerp.osv import osv, fields, expression
import logging

_logger = logging.getLogger(__name__)

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _get_payref(self,cr, uid, ids,field_name, arg,context=None):
        res={}
        _logger.info('------------begin--------')
        _logger.info(ids)
        for invoice_object in self.browse(cr, uid, ids, context=context):
            complain_name=invoice_object.origin
            _logger.info(complain_name)
            if complain_name:
                complain_obj=self.pool['ebiz.customer.complain']
                complain_id=complain_obj.search(cr, uid,[('name','=',complain_name)], context=context)
                complain=complain_obj.browse(cr, uid, complain_id, context=context)
                # _logger.info('------------123-------')
                # order_obj=self.pool['sale.order']
                # _logger.info('------------234------')

                res[invoice_object.id] =complain.order_id.payment_lines.ref
        _logger.info('------------end--------')
        return res

    _columns = {
        'payref':fields.function( _get_payref,type='char',string= u'支付流水号'),
    }

