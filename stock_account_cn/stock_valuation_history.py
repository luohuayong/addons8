# -*- coding: utf-8 -*- #
from openerp import tools
from openerp.osv import osv, fields

class stock_history(osv.osv):
    _inherit = 'stock.history'

    _columns = {
        'invoice_state': fields.selection([("invoiced", u"已开票"),
            ("2binvoiced", u"待开票"),
            ("none", u"不开票")], u"开票状态" ),
        'picking_type': fields.many2one('stock.picking.type', u'移库类型'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                picking_type, 
                invoice_state, 
                location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                price_unit_on_quant,
                source
                FROM
                ((SELECT
                    stock_move.id::text || '-' || quant.id::text AS id,
                    quant.id AS quant_id,
                    stock_move.id AS move_id,
                    stock_picking.picking_type_id AS picking_type,
                    stock_move.invoice_state AS invoice_state, 
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_quant as quant, stock_quant_move_rel, stock_move
                LEFT JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                LEFT JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                LEFT JOIN
                    product_product ON product_product.id = stock_move.product_id
                LEFT JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                LEFT JOIN
                    stock_picking ON stock_picking.id = stock_move.picking_id
                WHERE stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit') AND stock_quant_move_rel.quant_id = quant.id
                AND stock_quant_move_rel.move_id = stock_move.id AND ((source_location.company_id is null and dest_location.company_id is not null) or
                (source_location.company_id is not null and dest_location.company_id is null) or source_location.company_id != dest_location.company_id)
                ) UNION
                (SELECT
                    '-' || stock_move.id::text || '-' || quant.id::text AS id,
                    quant.id AS quant_id,
                    stock_move.id AS move_id,
                    stock_picking.picking_type_id AS picking_type,
                    stock_move.invoice_state AS invoice_state, 
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_quant as quant, stock_quant_move_rel, stock_move
                LEFT JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                LEFT JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                LEFT JOIN
                    product_product ON product_product.id = stock_move.product_id
                LEFT JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                LEFT JOIN
                    stock_picking ON stock_picking.id = stock_move.picking_id
                WHERE stock_move.state = 'done' AND source_location.usage in ('internal', 'transit') AND stock_quant_move_rel.quant_id = quant.id
                AND stock_quant_move_rel.move_id = stock_move.id AND ((dest_location.company_id is null and source_location.company_id is not null) or
                (dest_location.company_id is not null and source_location.company_id is null) or dest_location.company_id != source_location.company_id)
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_categ_id, date, price_unit_on_quant, source, picking_type, invoice_state 
            )""")

