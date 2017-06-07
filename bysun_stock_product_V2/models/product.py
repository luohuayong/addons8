# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import logging
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class product_product(osv.Model):
    _inherit = 'product.product'

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        context = context or {}
        field_names = field_names or []

        domain_products = [('product_id', 'in', ids)]
        domain_quant, domain_move_in, domain_move_out = self._get_domain_locations(cr, uid, ids, context=context)
        domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel'))] + domain_products
        domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel'))] + domain_products
        domain_quant += domain_products
        if context.get('lot_id') or context.get('owner_id') or context.get('package_id'):
            if context.get('lot_id'):
                domain_quant.append(('lot_id', '=', context['lot_id']))
            if context.get('owner_id'):
                domain_quant.append(('owner_id', '=', context['owner_id']))
            if context.get('package_id'):
                domain_quant.append(('package_id', '=', context['package_id']))
            moves_in = []
            moves_out = []
        else:
            moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty'], ['product_id'], context=context)
            moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty'], ['product_id'], context=context)

        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant, ['product_id', 'qty'], ['product_id'], context=context)
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))
        res = {}
        for id in ids:
            res[id] = {
                'qty_available': quants.get(id, 0.0),
                'incoming_qty': moves_in.get(id, 0.0),
                'outgoing_qty': moves_out.get(id, 0.0),
                'virtual_available': quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0),
                'sale_available': quants.get(id, 0.0) - moves_out.get(id, 0.0),
            }

        return res

    def _get_product_warehouse_location(self, cr, uid, ids, context=None):
        res = {}
        partner_model = self.pool['res.partner']
        warehouse_model = self.pool['stock.warehouse']
        for record in self.read(cr, uid, ids, ['seller_id'], context=context):
            if record['seller_id']:
                warehouse_id = partner_model.read(cr, uid, record['seller_id'][0], ['stock_warehouse_id'], context=context)
                if warehouse_id['stock_warehouse_id']:
                    location_id = warehouse_model.read(cr, uid, warehouse_id['stock_warehouse_id'][0], ['lot_stock_id'], context=context)
                    res[record['id']] = location_id['lot_stock_id'] and location_id['lot_stock_id'][0] or False
                else:res[record['id']] = False
            else:
                res[record['id']] = False
        return res

    def _product_available_display(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}
        stock_location_ids = self._get_product_warehouse_location(cr, uid, ids, context=context)
        for location in stock_location_ids:
            ctx = context.copy()
            if stock_location_ids[location]:
                ctx.update({'location':[stock_location_ids[location]]})
            qty = self.read(cr, uid, location, ['qty_available','outgoing_qty'], context=ctx)
            res[location] = qty['qty_available'] - qty['outgoing_qty']
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in ('qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty','sale_available'), 'Invalid domain left operand'
            assert operator in ('<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(value, (float, int)), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            product_ids = self.search(cr, uid, [], context=context)
            ids = []
            if product_ids:
                #TODO: use a query instead of this browse record which is probably making the too much requests, but don't forget
                #the context that can be set with a location, an owner...
                for element in self.browse(cr, uid, product_ids, context=context):
                    if eval(str(element[field]) + operator + str(value)):
                        ids.append(element.id)
            res.append(('id', 'in', ids))
        return res

    def action_sync_qty(self, cr, uid, ids, context=None):
        ebiz_stock_model = self.pool['ebiz.stock']
        ebiz_shop_model = self.pool['ebiz.shop']
        partner_model = self.pool['res.partner']
        warehouse_model = self.pool['stock.warehouse']
        if not isinstance(ids,list):
            ids = [ids]
        ebiz_stock_ids = []
        for product in self.read(cr, uid, ids, ['seller_id'], context=context):
            seller_id = product['seller_id'] and product['seller_id'][0] or False
            partner_id = partner_model.read(cr, uid, seller_id, ['stock_warehouse_id']) or {}
            warehouse_id = partner_id.get('stock_warehouse_id',False) and partner_id['stock_warehouse_id'][0] or False
            location_id = warehouse_model.read(cr, uid, warehouse_id, ['lot_stock_id']) or {}
            lot_stock_id = location_id.get('lot_stock_id',False) and location_id['lot_stock_id'][0] or 1
            # view_location_id = location_id.get('view_location_id',False) and location_id['view_location_id'][0] or 1
            ctx = context.copy()
            ctx.update({'location':[lot_stock_id]})
            sale_available = self.read(cr, uid, product['id'], ['sale_available'], context=ctx)
            exist_id = ebiz_stock_model.search(cr, uid, [('var_qty','=',0),('sync_check','=',True),('product_id','=',product['id'])])
            if exist_id:
                ebiz_stock_model.write(cr, uid, exist_id, {'stock_qty':sale_available['sale_available']})
                ebiz_stock_ids += exist_id
            else:
                ebiz_shop = ebiz_shop_model.search(cr, uid, [])
                ebiz_stock_id = ebiz_stock_model.create(cr, uid, {
                    'shop_id':ebiz_shop and ebiz_shop[0] or False,
                    'location_id':lot_stock_id,
                    'sync_check':True,
                    'stock_qty':sale_available['sale_available'],
                    'product_id':product['id'],
                    })
                ebiz_stock_ids.append(ebiz_stock_id)
        return ebiz_stock_ids

    _columns = {
    	'sale_available':fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string=u'可售数量',
            fnct_search=_search_product_quantity,
         	),
        'sale_available_display':fields.function(_product_available_display,
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string=u'可售数量',),
        'qty_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Quantity On Hand',
            fnct_search=_search_product_quantity,
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Forecast Quantity',
            fnct_search=_search_product_quantity,
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored in this location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Incoming',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to arrive.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods arriving to this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods arriving to the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods arriving to any Stock "
                 "Location with 'internal' type."),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Outgoing',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to leave.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods leaving this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods leaving the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods leaving any Stock "
                 "Location with 'internal' type."),
    }

product_product()

class product_template(osv.osv):
    _inherit = 'product.template'

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                # "reception_count": sum([p.reception_count for p in product.product_variant_ids]),
                # "delivery_count": sum([p.delivery_count for p in product.product_variant_ids]),
                "sale_available_display":sum([p.sale_available_display for p in product.product_variant_ids]),
                "qty_available": sum([p.qty_available for p in product.product_variant_ids]),
                "virtual_available": sum([p.virtual_available for p in product.product_variant_ids]),
                "incoming_qty": sum([p.incoming_qty for p in product.product_variant_ids]),
                "outgoing_qty": sum([p.outgoing_qty for p in product.product_variant_ids]),
                "sale_available": sum([p.sale_available for p in product.product_variant_ids]),
            }
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        prod = self.pool.get("product.product")
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in ('qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty','sale_available'), 'Invalid domain left operand'
            assert operator in ('<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(value, (float, int)), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            product_ids = prod.search(cr, uid, [], context=context)
            ids = []
            if product_ids:
                #TODO: use a query instead of this browse record which is probably making the too much requests, but don't forget
                #the context that can be set with a location, an owner...
                for element in prod.browse(cr, uid, product_ids, context=context):
                    if eval(str(element[field]) + operator + str(value)):
                        ids.append(element.id)
            res.append(('product_variant_ids', 'in', ids))
        return res

    _columns = {
        'sale_available': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string=u'可售数量'),
        'sale_available_display': fields.function(_product_available, multi='qty_available', type='float', string=u'可售数量'),
        'qty_available': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Quantity On Hand'),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Quantity Available'),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Incoming'),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Outgoing'),
        'name': fields.char('Name', required=True, translate=False, select=True),
        'is_combination': fields.boolean(u'是否组合商品', default=False),
    }

product_template()

