# -*- encoding: utf-8 -*-

from openerp import tools
from openerp.osv import osv, fields

class stock_cost_adjust(osv.osv):

    _inherit = "stock.cost.adjust"

    def onchange_origin_cost(self, cr, uid, ids, move_id,context=None):

        if context is None:
            context = {}

        res = {'value': {'origin_cost':0.0}}

        if move_id:
            #print move_id
            cr.execute("select sq.cost as cost from stock_quant as sq join stock_quant_move_rel as sqmr on sq.id = sqmr.quant_id where move_id = %s", (move_id, ))
            res_cost = cr.fetchall()
            #print res_cost
            if res_cost:
                for cost in res_cost:
                    #print cost
                    #print type(cost)
                    res['value']['origin_cost'] = float(cost[0])
        return res