# -*- encoding: utf-8 -*-
import time
from openerp import pooler
import logging
import traceback
from openerp import tools,api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from openerp.osv import fields,osv

class stock_inventory(osv.osv):

    _inherit = 'stock.inventory'

    _columns = {
        'error_code':fields.text(u'错误条码'),
        'same_code':fields.text(u'冲突条码'),
    }

    def _get_inventory_location(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.partner_id and user.partner_id.stock_location:
            return user.partner_id.stock_location.id
        return False

    _defaults = {
        'location_id':_get_inventory_location,
    }

    def action_open_wizard(self, cr, uid, ids, context=None):
        return {
            'name': '快速盘点',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'stock.inventory.simple',
            'type':'ir.actions.act_window',
            'target':'new',
        }
