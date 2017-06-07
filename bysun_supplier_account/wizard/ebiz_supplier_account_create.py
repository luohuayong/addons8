# -*- coding: utf-8 -*- #
import time
from openerp.osv import osv, fields
import logging
import openerp.addons.decimal_precision as dp

logger = logging.getLogger(__name__)

class ebiz_supplier_account_create(osv.osv_memory):
    _name = 'ebiz.supplier.account.create.wizard'
    _description = "Ebiz Supplier Account"

    def create_supplier_action(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids',False)
        supplier_ids = self.pool['ebiz.supplier.account.line'].create_ebiz_supplier_account_line(cr, uid, active_ids, context=context)
        return {
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'ebiz.supplier.account.line',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',supplier_ids or [0])],
        }
ebiz_supplier_account_create()
