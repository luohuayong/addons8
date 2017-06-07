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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class stock_picking_to_wave(osv.osv_memory):
    _inherit = 'stock.picking.to.wave'

    _columns = {
        'wave_id': fields.many2one('stock.picking.wave', 'Picking Wave' ),
        'carrier': fields.many2one('delivery.carrier', 'Delivery Route' )
    }

    def attach_pickings(self, cr, uid, ids, context=None):
        #use active_ids to add picking line to the selected wave
        wave_wizard = self.browse(cr, uid, ids, context=context)[0]
        wave_id = wave_wizard.wave_id
        carrier = wave_wizard.carrier and wave_wizard.carrier.id or False
        if not wave_id:
            vals = {}
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'pick.wave') or '/'
            vals['state'] = 'done'
            wave_id = self.pool.get('stock.picking.wave').create(cr, uid, vals)
        else:
            wave_id = wave_id.id
        picking_ids = context.get('active_ids', False)
        write_vals = {'wave_id':wave_id}
        if carrier:write_vals.update(carrier_id=carrier)
        return self.pool.get('stock.picking').write(cr, uid, picking_ids, write_vals)