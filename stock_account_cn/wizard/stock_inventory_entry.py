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

class stock_inventory_entry(osv.osv_memory):
    _name = "stock.inventory.entry"
    _description = "Create account entry base inventory"
    _columns = {
        'period_id' : fields.many2one('account.period', '会计期间', required=True),
        'journal_id': fields.many2one('account.journal', '账簿', required=True ),
        'account_id' : fields.many2one('account.account', '会计科目', required=True),
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
        res = super(stock_inventory_entry, self).default_get(cr, uid, fields, context=context)
        period_id = self.pool.get('account.period').find(cr, uid,  datetime.now(), context=context)[0]
        res['period_id'] = period_id
        account_ids = self.pool.get('account.account').search(cr, uid, [('name','ilike','损溢')], context=context)
        res['account_id'] = account_ids and account_ids[0]

        try:
            model, journal_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock_account', 'stock_journal')
            res['journal_id'] = journal_id
        except (orm.except_orm, ValueError):
            pass
        return res

    def create_inventory_entry(self, cr, uid, ids, context=None):
        inventory_obj = self.pool.get('stock.inventory')
        wiz = self.browse(cr, uid, ids[0])
        period_id = wiz.period_id.id
        journal_id = wiz.journal_id.id
        account_id = wiz.account_id.id
        inventory_ids = context.get('active_ids', False)
        inventory_obj.create_inventory_entry(cr, uid, inventory_ids, account_id, period_id, journal_id, context = context)
        
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
