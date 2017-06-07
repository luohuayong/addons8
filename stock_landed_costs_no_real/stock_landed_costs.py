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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class stock_landed_cost(osv.osv):
    _inherit = 'stock.landed.cost'

    def get_valuation_lines(self, cr, uid, ids, picking_ids=None, context=None):
        picking_obj = self.pool.get('stock.picking')
        lines = []
        if not picking_ids:
            return lines

        for picking in picking_obj.browse(cr, uid, picking_ids):
            for move in picking.move_lines:
               #it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.cost_method != 'real':
                    continue
                total_cost = 0.0
                total_qty = move.product_qty
                weight = move.product_id and move.product_id.weight * move.product_qty
                volume = move.product_id and move.product_id.volume * move.product_qty
                for quant in move.quant_ids:
                    total_cost += quant.cost * quant.qty
                vals = dict(product_id=move.product_id.id, move_id=move.id, quantity=move.product_uom_qty, former_cost=total_cost, weight=weight, volume=volume)
                lines.append(vals)
        if not lines:
            raise osv.except_osv(_('Error!'), _('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured with real price costing method. Please make sure it is the case, or you selected the correct picking'))
        return lines

    def button_validate(self, cr, uid, ids, context=None):
        quant_obj = self.pool.get('stock.quant')

        for cost in self.browse(cr, uid, ids, context=context):
            if not cost.valuation_adjustment_lines or not self._check_sum(cr, uid, cost, context=context):
                raise osv.except_osv(_('Error!'), _('You cannot validate a landed cost which has no valid valuation lines.'))

            move_id = False
            quant_dict = {}
            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit
                quants = [quant for quant in line.move_id.quant_ids]
                for quant in quants:
                    if quant.id not in quant_dict:
                        quant_dict[quant.id] = quant.cost + diff
                    else:
                        quant_dict[quant.id] += diff
                for key, value in quant_dict.items():
                    quant_obj.write(cr, uid, key, {'cost': value}, context=context)
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
                if line.move_id.product_id.valuation == 'real_time':
                    if not move_id: move_id = self._create_account_move(cr, uid, cost, context=context)
                    self._create_accounting_entries(cr, uid, line, move_id, qty_out, context=context)
            self.write(cr, uid, cost.id, {'state': 'done', 'account_move_id': move_id or False}, context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
