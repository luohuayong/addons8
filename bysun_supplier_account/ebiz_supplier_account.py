# -*- encoding: utf-8 -*-

import logging
import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools, exceptions
from openerp.osv import fields, osv, expression
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp import workflow
import re

_logger = logging.getLogger(__name__)
class ebiz_supplier_account_line(osv.osv):

    _name = "ebiz.supplier.account.line"
    _inherit = ['mail.thread','ir.needaction_mixin']
    _order = "product_id,partner_id desc"
    _description = u"供应商结算项"

    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        result = {}        
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.amount * obj.unit_price
        return result

    def _get_purchase_total(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.amount * obj.standard_price
        return result

    def _get_supplier_ids(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        supplier_account_model = self.pool['ebiz.supplier.account.line']
        return supplier_account_model.search(cr, uid, [('move_id','in',ids)])

    _columns = {
        'invoice_id':fields.many2one('account.invoice',u'发票',),
        'partner_id':fields.many2one('res.partner', u'供应商', required=True,),
        'origin':fields.char(u'源单据',),
        'sale_id':fields.many2one('sale.order',u'销售订单',),
        'picking_id':fields.many2one('stock.picking',u'调拨单',),
        'move_id':fields.many2one('stock.move','Move',),
        'product_id':fields.many2one('product.product',u'产品', required=True,),
        'uom_id':fields.many2one('product.uom',u'单位',),
        'amount':fields.float(u'数量',required=True,default=1, states={'draft': [('readonly', False)]}, track_visibility='onchange',),
        'unit_price':fields.float(u'销售单价',states={'draft': [('readonly', False)]}, track_visibility='onchange',),
        'subtotal':fields.function(_get_subtotal,string=u'销售金额',type='float',store=True,),
        'standard_price':fields.float(u'采购单价', required=True, states={'draft': [('readonly', False)]},  track_visibility='onchange',),
        'purchase_total': fields.function(_get_purchase_total,string=u'采购金额',type='float',store=True,),
        'type':fields.selection([('payment_goods',u'货款'),('cost',u'费用'),('return_goods',u'退货')],u'类型',),
        'commission':fields.float(u'佣金',default=0.00),
        'supplier_mode':fields.selection([('Direct_Procurement',u'直采'),('Consign_stock_in',u'代售入仓'),('Consign',u'代售不入仓'),('Commission',u'佣金')],u'供应商类型',),
        'state':fields.selection([('draft',u'未对账'),('checked',u'已对账'),('settled',u'已结算'),('cancelled',u'已取消')],u'状态',),
        'notes':fields.text(u'备注',required=True,),
        'active':fields.boolean(u'有效'),
        'statement_no': fields.char(u'对账单编号'),
        'qty_send':fields.related('move_id','date',type='datetime',string=u'出库时间', readonly=True,
            store={
                'ebiz.supplier.account.line': (lambda self,c,u,ids,context:ids, ['move_id'], 10),
                'stock.move':(_get_supplier_ids, ['date'],10),
            }),
        'name':fields.char(u'供应商结算项编号'),
    }

    _defaults = {
        'active':True,
        'state': 'draft',
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        result = {'value':{'supplier_mode':False}}
        if partner_id:
            partner_model = self.pool['res.partner']
            partner = partner_model.browse(cr, uid, partner_id)
            result['value'].update({'supplier_mode':partner.supplier_mode})
        return result

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        result = {'value':{'uom_id':False}}
        if product_id:
            product_model = self.pool['product.product']
            product = product_model.browse(cr, uid, product_id)
            result['value'].update({'uom_id':product.uom_id and product.uom_id.id or False})
        return result

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for line in self.browse(cr, uid, ids, context=context):        
            result.append((line.id, (line.origin or '') + (line.name or '')))
        return result

    def create(self, cr, uid, vals, context=None):
        product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gysbt')
        if product_id:
            product_id = product_id[1]
            if context.get('default_product_id', False) == product_id or vals.get('product_id', False) == product_id:
                if vals.get('standard_price') <= 0 or vals.get('amount') <= 0:
                    raise exceptions.ValidationError(u'数量和单价必须大于0！')
        if not vals.get('name',''):
            sequence = self.pool.get('ir.sequence').get(cr, uid, 'ebiz.supplier.account.no', context=context)
            vals.update({'name':sequence})
        return super(ebiz_supplier_account_line, self).create(cr, uid, vals, context)

    def action_settled(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            obj.write({'state':'settled'})
        return True

    def action_checked(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            obj.write({'state':'checked'})
        return True

    def action_cancelled(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.state == 'draft':
                obj.write({'state':'cancelled'})
                self.pool.get('stock.move').write(cr, uid, obj.move_id.id, {'is_import_supplier_account':False})
        return True

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            res = {'supplier_mode': partner.supplier_mode or ''}
        return {'value':res}

    def create_ebiz_supplier_account_line_from_move(self, cr, uid, sale_objs, picking, origin_move, move, customer_location, total_move_qty, is_combination, context=None):
        new_ids = []
        now_date = time.strftime("%Y-%m-%d")
        if not is_combination and move.is_import_supplier_account:
            _logger.info("is_combination and is_import_supplier_account%s"%move.id)
            return new_ids
        partner = self.get_partner_id(cr, uid, move.product_id.id, context=context)
        if not partner:
            _logger.info("not partner%s"%move.id)
            return new_ids
            #raise osv.except_osv(_(u'警告!'), _(u'产品【%s】的供应商没有维护！'%move.product_id.name))

        #此处应该判断原始的move
        # if not is_combination and move.location_id.id != customer_location and move.location_dest_id.id != customer_location and \
        #         not move.location_id.scrap_location and not move.location_dest_id.scrap_location:
        #     _logger.info("===not customer_location or scrap_location%s"%move.id)
        #     move.write({'is_import_supplier_account':True})
        #     return new_ids
        if partner.supplier_mode == 'Direct_Procurement':
            _logger.info("====Direct_Procurement%s"%move.id)
            move.write({'is_import_supplier_account':True})
            return new_ids

        ebiz_type = 'payment_goods'
        #原始的move单据，源库位是客户库位，退货
        if origin_move.location_id.id == customer_location:
            ebiz_type = 'return_goods'
        # for quant in move.quant_ids:
        #     if quant.qty < 0:
        #         _logger.info("========quant < 0%s"%move.id)
        #         return new_ids
            # 可能会有加工单等出现move的数量大于实际出库的数量，以实际出库的数量为准
        if ebiz_type == 'payment_goods' and total_move_qty <= 0:
            return new_ids

        pricelist_id = partner.property_product_pricelist_purchase.id
        standard_price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], move.product_id.id, move.product_uom_qty or 1.0, partner.id or False, {'uom': move.product_uom.id, 'date': now_date})[pricelist_id]
        _logger.info("standard_price:%s"%standard_price)
        # standard_price = quant.cost
        # supplier.property_product_pricelist_purchase.id
        unit_price = 0
        sale_id = picking.sale_id and picking.sale_id.id or False
        for sale_obj in sale_objs:
            if not sale_id:
                sale_id = sale_obj.id
            for line in sale_obj.order_line:
                if (line.product_id == move.product_id):
                    unit_price = line.price_unit

        amount = ebiz_type == 'return_goods' and - move.product_uom_qty or ebiz_type == 'payment_goods' and move.product_uom_qty or 0
        if is_combination:amount = (amount / is_combination) * total_move_qty
        # if ebiz_type == 'payment_goods':
        #     if amount > total_move_qty:
        #         amount = total_move_qty
            # total_move_qty -= amount
        commission = partner.supplier_mode == 'Commission' and amount * unit_price - standard_price * amount
        # if commission < 0:
        #     commission = 0
        vals = {
            'partner_id': partner.id ,
            'product_id': move.product_id and move.product_id.id or False,
            'picking_id': picking.id,
            'uom_id': move.product_uom and move.product_uom.id or False,
            'amount': amount,
            'unit_price': unit_price or 0,
            'sale_id': sale_id,
            'type': ebiz_type or '',
            'move_id': origin_move.id or False,
            'commission':commission,
            'state': 'draft',
            'standard_price':standard_price,
            'notes':move.name,
            'supplier_mode': partner.supplier_mode,
        }
        new_id = self.pool.get('ebiz.supplier.account.line').create(cr, uid, vals,context=context)
        new_ids.append(new_id)
        #原始的move写标志
        origin_move.write({'is_import_supplier_account':True})
        _logger.info("=new_ids%s"%new_ids)
        return new_ids

    def create_ebiz_supplier_account_line(self, cr, uid, picking_ids=False, context=None):
        res = []
        now_date = time.strftime('%Y-%m-%d')
        new_ids = []
        data_model = self.pool.get('ir.model.data')
        # picking_type_id = data_model.get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_customer_complain_picking_type_th')
        customer_location = data_model.get_object_reference(cr, uid, 'stock', 'stock_location_customers')
        # picking_type_id = picking_type_id and picking_type_id[1] or False
        customer_location = customer_location and customer_location[1] or False
        for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids, context=context):
            if picking.picking_type_id.code == 'internal':
                _logger.info("=========internal%s"%picking.name)
                continue
            sale_objs = picking.sale_id
            if (len(sale_objs) == 0):
                sale_ids = self.pool.get('sale.order').search(cr, uid, [('name', '=', picking.origin)], context=context)
                sale_objs = self.pool.get('sale.order').browse(cr, uid, sale_ids, context=context)
            for move in picking.move_lines:
                if move.state == 'cancel':
                    move.write({'is_import_supplier_account':True})
                    continue

                if move.state != 'done':
                    continue

                if move.is_import_supplier_account:
                    _logger.info("=========is_supplier_account%s"%move.id)
                    continue
                if move.location_id.id != customer_location and move.location_dest_id.id != customer_location and \
                    not move.location_id.scrap_location and not move.location_dest_id.scrap_location:
                    _logger.info("===not customer_location or scrap_location%s"%move.id)
                    move.write({'is_import_supplier_account':True})
                    continue
                    #raise osv.except_osv(_(u'警告!'), _(u'单据【%s】中产品【%s】对应的 MOVE 已经导入过供应商结算项！'%(picking.name,move.product_id.name,)))
                if move.product_id.is_combination:
                    _logger.info("1111111111111111is_combination")
                    for quant in move.quant_ids:
                        if not quant.lot_id:
                            continue
                        production_ids = self.pool.get('stock.production').search(cr, uid, [('stock_lot', '=', quant.lot_id.id)], context=context)
                        production_id = production_ids and production_ids[0] or False
                        if production_id:
                            for production_obj in self.pool.get('stock.production').browse(cr, uid, [production_id], context=context):
                                combination_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('origin', '=', production_obj.name)], context=context)
                                for picking_line in self.pool.get('stock.picking').browse(cr, uid, combination_picking_ids, context=context):
                                    if picking_line.picking_type_id.code == 'outgoing':
                                        for move_line in picking_line.move_lines:
                                            ids = self.create_ebiz_supplier_account_line_from_move(cr, uid, sale_objs, picking, move, move_line, customer_location, quant.qty, move.product_id.is_combination and production_obj.product_uom_qty or 0, context=context)
                                            new_ids += ids
                else:
                    _logger.info("22222222222not is_combination")
                    new_ids_1 = self.create_ebiz_supplier_account_line_from_move(cr, uid, sale_objs, picking, move, move, customer_location, move.product_uom_qty, False, context=context)
                    new_ids += new_ids_1
        return new_ids

    def get_partner_id(self, cr, uid, product_id=False, context=None):
        partner = False
        if product_id:
            for seller in self.pool.get('product.product').browse(cr, uid, product_id).seller_ids:
                if not partner:
                    partner = seller.name 
        return partner

    def _prepare_for_invoice_goods(self, cr ,uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        sql = """
                select
                partner_id,product_id,standard_price,uom_id,sum(amount) as amount,sum(amount * standard_price) as total_price
                from
                ebiz_supplier_account_line
                where
                id in %s
                group by partner_id,product_id,standard_price,uom_id"""
        cr.execute(sql,(tuple(ids),))
        res = cr.dictfetchall()
        product_model = self.pool.get('product.product')
        lines = []
        for obj in res:
            product = product_model.browse(cr, uid, obj['product_id'])
            inv_lines = {
                'product_id':obj['product_id'] or False,
                'uos_id':obj['uom_id'] or False,
                'quantity':obj['amount'] or 0.00,
                'price_unit':obj['standard_price'] or 0.00,
                'name':product.name or '/',
                'account_id':product.property_account_expense and product.property_account_expense.id or product.categ_id.property_account_expense_categ.id,
            }
            lines.append((0,0,inv_lines))
        return lines

    def _prepare_for_invoice_cost(self, cr ,uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        sql = """
                select
                partner_id,product_id,uom_id,type,sum(amount) as amount,sum(amount * standard_price) as total_price
                from
                ebiz_supplier_account_line
                where
                id in %s
                group by partner_id,product_id,uom_id,type"""
        cr.execute(sql,(tuple(ids),))
        res = cr.dictfetchall()
        model_data = self.pool['ir.model.data']
        product_model = self.pool.get('product.product')
        product_bt = model_data.get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gysbt')
        product_kk = model_data.get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gyskk')
        product_bt = product_model.browse(cr, uid, product_bt[1])
        product_kk = product_model.browse(cr, uid, product_kk[1])
        lines = []
        for obj in res:
            product = product_model.browse(cr, uid, obj['product_id'])
            inv_lines = {
                'product_id':obj['product_id'] or False,
                'uos_id':obj['uom_id'] or False,
                'quantity':product_bt.id == product.id and 1 or product_kk.id == product.id and -1 or 0.00,
                'price_unit':abs(obj['total_price']) or 0.00,
                'name':product.name or '/',
                'account_id':product.property_account_expense and product.property_account_expense.id or product.categ_id.property_account_expense_categ.id,
            }
            lines.append((0,0,inv_lines))
        return lines

    def _prepare_for_invoice_commision(self, cr ,uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        sql = """
                select
                partner_id,product_id,unit_price,uom_id,sum(amount) as amount,sum(COALESCE(commission, 0.00)) as commission,sum(amount * unit_price) as total_price
                from
                ebiz_supplier_account_line
                where
                id in %s
                group by partner_id,product_id,unit_price,uom_id"""
        product_model = self.pool.get('product.product')
        product_yj = self.pool['ir.model.data'].get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gysyj')
        product_yj = product_model.browse(cr, uid, product_yj[1])

        lines = []
        cr.execute(sql,(tuple(ids),))
        res = cr.dictfetchall()
        inv_lines_commission = {
                'product_id':product_yj.id or False,
                'uos_id':product_yj.uom_id and product_yj.uom_id.id or False,
                'quantity':-1,
                'price_unit':0.00,
                'name':u'佣金',
                'account_id':product_yj.property_account_income and product_yj.property_account_income.id or product_yj.categ_id.property_account_income_categ.id,
            }
        commission = 0.00
        for obj in res:
            commission += obj.get('commission',0.00)
            # if commission < 0 :
            #     commission = 0
            product = product_model.browse(cr, uid, obj['product_id'])
            inv_lines = {
                'product_id':obj['product_id'] or False,
                'uos_id':obj['uom_id'] or False,
                'quantity':obj['amount'] or 0.00,
                'price_unit':obj['unit_price'] or 0.00,
                'name':product.name or '/',
                'account_id':product.property_account_expense and product.property_account_expense.id or product.categ_id.property_account_expense_categ.id,
            }
            lines.append((0,0,inv_lines))
        inv_lines_commission.update({
                    'price_unit':commission,
                })
        lines.append((0,0,inv_lines_commission))
        return lines

    def create_account_invoice(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        no_checked_ids = self.search(cr, uid, [('state','!=','checked'),('id','in',ids)])
        if no_checked_ids:
            raise osv.except_osv(_(u'警告!'), _(u'必须选择已对账的结算项创建供应商发票！'))
        statement_no = 'statement_no'
        for line in self.browse(cr, uid, ids, context=context):
            if statement_no == 'statement_no':
                statement_no = line.statement_no
                state = line.state
                continue
            if state != 'checked':
                raise osv.except_osv(_(u'警告!'), _(u'必须选择已对账的结算项创建供应商发票！'))
            if statement_no != line.statement_no:
                raise osv.except_osv(_(u'警告!'), _(u'只能选择一个对账单创建供应商发票！'))
        cr.execute("""select partner_id,supplier_mode from ebiz_supplier_account_line where id in %s""",(tuple(ids),))
        res_partner = cr.fetchall()
        res_partner = set(res_partner and [(p[0],p[1]) for p in res_partner] or [])
        if len(res_partner) != 1:
            raise osv.except_osv(_(u'警告!'), _(u'请选择同一个供应商的结算项进行创建供应商发票！'))
        res_partner = [p for p in res_partner]
        
        partner = res_partner[0][0]
        partner = self.pool['res.partner'].browse(cr, uid, partner)

        lines = []

        payment_return_ids = self.search(cr, uid, [('type','in',['payment_goods','return_goods']),('id','in',ids)])
        cost_ids = self.search(cr, uid, [('type','=','cost'),('id','in',ids)])
        if partner.supplier_mode == 'Commission':
            if payment_return_ids:
                payment_return_lines = self._prepare_for_invoice_commision(cr, uid, payment_return_ids, context=context)
                lines += payment_return_lines
            if cost_ids:
                cost_lines = self._prepare_for_invoice_cost(cr, uid, cost_ids, context=context)
                lines += cost_lines
        else:
            if payment_return_ids:
                payment_return_lines = self._prepare_for_invoice_goods(cr, uid, payment_return_ids, context=context)
                lines += payment_return_lines
            if cost_ids:
                cost_lines = self._prepare_for_invoice_cost(cr, uid, cost_ids, context=context)
                lines += cost_lines

        journal_id = self.pool.get('account.journal').search(cr, uid, [('type','=','purchase')],)
        vals = {
            'type':'in_invoice',
            'state': 'draft',
            'partner_id':partner.id,
            'account_id':partner.property_account_payable and partner.property_account_payable.id or False,
            'journal_id':journal_id and journal_id[0] or 5,
            'date_invoice':time.strftime('%Y-%m-%d'),
            'invoice_line':lines,
            'origin': statement_no,
        }
        invoice_id = self.pool.get('account.invoice').create(cr, uid, vals)
        # 把生成的发票写入到勾选的供应商结算项中，方面数据查询。
        self.write(cr, uid, ids, {'invoice_id':invoice_id, 'state':'settled'})
        return invoice_id

ebiz_supplier_account_line()


class stock_move(osv.osv):

    _inherit = "stock.move"

    _columns = {
        'is_import_supplier_account':fields.boolean(u'已导入结算项', change_default=False),
    }

stock_move()

class stock_picking(osv.osv):

    _inherit = "stock.picking"

    def _get_sale_id(self, cr, uid, ids, name, args, context=None):
        sale_obj = self.pool.get("sale.order")
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = False
            if picking.group_id:
                sale_ids = sale_obj.search(cr, uid, [('procurement_group_id', '=', picking.group_id.id)], context=context)
                if sale_ids:
                    res[picking.id] = sale_ids[0]
        return res

    def _order_ids_from_picking(self, cr, uid, ids, context=None):
        cr.execute("""select distinct id From stock_picking where sale_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]

    def _get_buyer_memo(self, cr, uid, ids, field_name, arg, context=None):
        return super(stock_picking, self)._get_buyer_memo(cr, uid, ids, field_name, arg, context=context)

    def _get_seller_memo(self, cr, uid, ids, field_name, arg, context=None):
        return super(stock_picking, self)._get_seller_memo(cr, uid, ids, field_name, arg, context=context)

    _columns = {
        'sale_id': fields.function(_get_sale_id, type="many2one", relation="sale.order", string="Sale Order", store=True),

        'buyer_memo': fields.function(_get_buyer_memo, type="text", string=u'买家备注', store={
                'sale.order':(_order_ids_from_picking, ['note'], 10),
                'stock.picking':(lambda self, cr, uid, ids, c=None:ids,['sale_id'],10),
            }),
        'seller_memo': fields.function(_get_seller_memo, type="text", string=u'卖家备注', store={
                'sale.order':(_order_ids_from_picking, ['seller_memo'], 10),
                'stock.picking':(lambda self, cr, uid, ids, c=None:ids,['sale_id'],10),
            }),
    }

    def search_picking_ids(self, cr, uid, context=None):
        sql = """ select sp.id as picking_id
                    from stock_move sm
                        left join stock_picking sp on sp.id = sm.picking_id
                        left join stock_picking_type spt on sp.picking_type_id = spt.id
                    where spt.code in ('outgoing','incoming') and sp.state = 'done' and (sm.is_import_supplier_account = 'f' or sm.is_import_supplier_account is null)
                    group by sp.id
                    order by sp.id limit 600
            """
        cr.execute(sql)
        result = cr.fetchall()
        _logger.info(result)
        
        if not result or result is None:
            return {'type': 'ir.actions.act_window_close'}
        res = []
        for r in result:
            if r[0] not in res:
                res.append(r[0])
        self.pool.get('ebiz.supplier.account.line').create_ebiz_supplier_account_line(cr, uid, res,context=context)

    # def create(self, cr, uid, default, context=None):
    #     if default.get('move_lines',False):
    #         dict_line = default.get('move_lines',False)[0][2]
    #         product_id = dict_line.get('product_id',False)
    #         supplier_mode = ''
    #         if product_id:
    #             for seller in self.pool.get('product.product').browse(cr, uid, product_id).seller_ids:
    #                 if not supplier_mode:
    #                     supplier_mode = seller.name.supplier_mode 
    #         if supplier_mode == 'Direct_Procurement':
    #             default.update({'is_supplier_account':False})
    #     return super(stock_picking, self).create(cr, uid, default, context=context)

stock_picking()