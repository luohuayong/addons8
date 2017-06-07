# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools
from datetime import datetime

class stock_picking_entry(osv.osv_memory):
    _name = "stock.picking.entry"
    _description = u"基于入库/出库单创建会计凭证"
    _columns = {
        'account_id' : fields.many2one('account.account', u'会计科目', ),
        'period_id' : fields.many2one('account.period', u'会计期间', required=True),
        'journal_id': fields.many2one('account.journal', u'账簿', required=True ),
        'entry_type': fields.selection([('in', u'出库核算'), ('out', u'入库核算')], u'出库/入库', required=True ),
    }
    _defaults = {

    }

    def default_get(self, cr, uid, fields, context):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        res = super(stock_picking_entry, self).default_get(cr, uid, fields, context=context)
        period_id = self.pool.get('account.period').find(cr, uid,  datetime.now(), context=context)[0]
        res['period_id'] = period_id

        try:
            model, journal_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock_account', 'stock_journal')
            res['journal_id'] = journal_id
        except (orm.except_orm, ValueError):
            pass
        return res

    def create_receipt_entry(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        wiz = self.browse(cr, uid, ids[0])
        period_id = wiz.period_id.id
        journal_id = wiz.journal_id.id
        account_id = wiz.account_id and wiz.account_id.id
        picking_ids = context.get('active_ids', False)

        entry_ids = picking_obj.create_receipt_entry(cr, uid, picking_ids, period_id, journal_id, account_id, context = context)
        action_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'account.action_move_journal_line')
        action_pool = self.pool['ir.actions.act_window']
        action = action_pool.read(cr, uid, action_id, context=context)
        action['domain'] = "[('id','in', ["+','.join(map(str,entry_ids))+"])]"
        return action

    def create_delivery_entry(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        wiz = self.browse(cr, uid, ids[0])
        period_id = wiz.period_id.id
        journal_id = wiz.journal_id.id
        account_id = wiz.account_id and wiz.account_id.id
        picking_ids = context.get('active_ids', False)
        entry_ids = picking_obj.create_delivery_entry(cr, uid, picking_ids, period_id, journal_id, account_id, context = context)

        action_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'account.action_move_journal_line')
        action_pool = self.pool['ir.actions.act_window']
        action = action_pool.read(cr, uid, action_id, context=context)
        action['domain'] = "[('id','in', ["+','.join(map(str,entry_ids))+"])]"
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
