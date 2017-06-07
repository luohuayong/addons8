# -*- encoding: utf-8 -*-
import time
from openerp import pooler
import logging
import traceback
import json
from openerp.tools.translate import _
from openerp import tools,api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from openerp.osv import fields,osv

_logger = logging.getLogger(__name__)

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'pending': fields.boolean(u'挂起', readonly=True, copy=False ),
        'delivery_code':fields.char(u'配送编码', help=u'对应网站的id字段'),
        'delivery_date':fields.date(u'配送日期', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'delivery_hour':fields.char(u'配送时段', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
    }

    _defaults = {
        'pending': False,
    }

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(sale_order,self).action_cancel(cr, uid, ids, context)
        name=self.browse(cr,uid,ids[0],context).name
        idx=self.search(cr,uid,[('name','ilike',name+'-Cancel')])

        cancel='-Cancel'
        if len(idx)>0:
            cancel='-Cancel(%s)'%len(idx)
        self_care=name+cancel
        self.write(cr,uid,ids,{'name': self_care})
        return res

    def action_suspend(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            if order.shipped or order.state in ['cancel', 'done']:
                raise osv.except_osv(u'错误!', u'已发货、已取消、已完成的订单不可挂起/解挂!')
            pending = not order.pending
            picking_ids = [x.id for x in order.picking_ids]
            self.pool['stock.picking'].write(cr, uid, picking_ids, {'pending': pending}, context)
            self.write(cr, uid, order.id, {'pending': pending}, context)
            
        return True

    def return_order(self, cr, uid, vals, context=None):
        res = self.pool['stock.picking'].return_order(cr, uid, vals, context=context)
        return res

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    def _prepare_picking_assign(self, cr, uid, move, context=None):
        """ 多步出库时候，由Procurement Order产生Stock Picking时候，从SO上取得挂起字段，
             填入新产生的Picking
        """
        values = super(stock_move, self)._prepare_picking_assign(cr, uid, move, context=context)
        if move.group_id:
            so_ids = self.pool['sale.order'].search(cr, uid, [('name', '=', move.group_id.name)], context=context)
            if so_ids:
                so = self.pool['sale.order'].read(cr, uid, so_ids[0], ['pending',], context)
                values.update({'pending': so['pending'], })
        return values


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, toolbar=False, submenu=False, context=None):
        res = super(stock_picking, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu, context=context)
        if res.get('toolbar',{}):
            if res['name'] == 'stock.picking.tree':
                for index,action in enumerate(res['toolbar']['action']):
                    if action['res_model'] == 'delivery.order.print':
                        res['toolbar']['action'].pop(index)
                        break
            elif res['name'] == 'vpicktree_dadanjianhuo':
                for index,action in enumerate(res['toolbar']['action']):
                    if action['res_model'] == 'stock.picking.to.wave':
                        res['toolbar']['action'].pop(index)
                        break
        return res

    def _get_partner_address(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        partner_model = self.pool['res.partner']
        for record in self.read(cr, uid, ids, ['partner_id']):
            if record['partner_id']:
                address = partner_model.browse(cr, uid, record['partner_id'][0])
                stock_address = (address.state_id and address.state_id.name or '') + (address.city or '') + (address.street2 or '') + (address.street or '')
                result[record['id']] = stock_address
        return result

    def _get_buyer_memo(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            so_name = ''
            if (rec.origin and rec.origin.find(':') > 0):
                so_name = rec.origin[0:rec.origin.index(':')]
            else:
                so_name = rec.origin
            so_id = self.pool.get('sale.order').search(cr, uid, [('name', '=', so_name)], context=context)
            if so_id:
                so = self.pool.get('sale.order').browse(cr, uid, so_id, context=context)
                if so:
                    result[rec['id']] = so.note
        return result

    def _get_seller_memo(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            so_name = ''
            if (rec.origin and rec.origin.find(':') > 0):
                so_name = rec.origin[0:rec.origin.index(':')]
            else:
                so_name = rec.origin
            so_id = self.pool.get('sale.order').search(cr, uid, [('name', '=', so_name)], context=context)
            if so_id:
                so = self.pool.get('sale.order').browse(cr, uid, so_id, context=context)
                if so:
                    result[rec['id']] = so.seller_memo
        return result

    _columns = {
        'pending': fields.boolean(u'挂起', readonly=True, copy=False ),
        'address': fields.function(_get_partner_address, type="char", string="客户地址", store={
                'stock.picking':(lambda self, cr, uid, ids, context=None: ids, ['partner_id'], 10),
            }),
        'return_no':fields.char(u'退货单号'),
        'return_send':fields.boolean(u'退货状态已同步'),
        'delivery_code': fields.char(u'配送编码', help='对应网站的id字段'),
        'delivery_date': fields.char(u'配送日期', ),
        'delivery_hour': fields.char(u'配送时段', ),
        'buyer_memo': fields.function(_get_buyer_memo, type="text", string=u'买家备注', store=True),
        'seller_memo': fields.function(_get_seller_memo, type="text", string=u'卖家备注', store=True),
    }

    _defaults = {
        'return_no':'',
        'pending': False,
    }

    def create(self, cr, user, vals, context=None):
        if vals.get('origin', False):
            origin = vals.get('origin', '')
            index = origin.find(':')
            if index > 0:
                origin = origin[0: index]
            sale_ids = self.pool.get('sale.order').search(cr, user, [('name', '=', origin)], context=context)
            sale_id = sale_ids and sale_ids[0] or False
            if sale_id:
                for sale_obj in self.pool.get('sale.order').browse(cr, user, [sale_id], context=context):
                    vals.update({'seller_memo': sale_obj.seller_memo})

        return super(stock_picking, self).create(cr, user, vals, context)

    def get_sale_order(self, cr, uid, id, context=None):
        group_id = self.read(cr, uid, id, ['group_id'], context)
        # _logger.info("==============group_id=%s================" % (group_id, ))
        so_ids = self.pool['sale.order'].search(cr, uid, [('name', '=', group_id['group_id'] and group_id['group_id'][1])], context=context)
        return so_ids

    def get_picking_from_ref(self, cr, uid, ref, context=None):
        """ 根据单号返回picking id. 验货打包界面使用"""
        domain = [('state', 'in', ('assigned', 'partially_available')), ('name','=', ref)]
        picking_ids = self.search(cr, uid, domain, context=context)
        res = {}
        if picking_ids:
            for picking in self.read(cr, uid, picking_ids, ['pending', 'name']):
                if picking['pending']: raise osv.except_osv(u'警告!', u'发货单%s已经挂起，不允许打包!' % picking['name'])
            #self.do_prepare_partial(cr, uid, [ picking_ids[0] ], context=context)
            res = self.load_picking_from_ui(cr, uid, picking_ids[0], context=context)
        return res

    def load_picking_from_ui(self, cr, uid, picking_id, context=None):
        """ 返回指定 id 的picking详细信息. 验货打包界面使用"""
        res = {}
        pack_obj = self.pool.get('stock.pack.operation')
        package_obj = self.pool.get('stock.quant.package')
        ul_obj = self.pool.get('product.ul')
        product_obj = self.pool.get('product.product')
        lot_obj = self.pool.get('stock.production.lot')
        
        if context is None:
            context = {}
        picking = self.read(cr, uid, picking_id, [], context=context)
        res['picking'] = picking
        pack_ids = pack_obj.search(cr, uid, [('picking_id', '=', picking_id)], context=context)
        if not pack_ids:
            # 让系统创建Operation
            self.do_prepare_partial(cr, uid, [ picking_id ], context=context)
            pack_ids = pack_obj.search(cr, uid, [('picking_id', '=', picking_id)], context=context)
        if pack_ids:
            packs = pack_obj.read(cr, uid, pack_ids, [], context=context)
            res['packoplines'] = packs
            for op in packs:
                op['lot_name'] = ''
                op['lot_ref'] = ''
                if op['lot_id']:
                    lots_codes = lot_obj.read(cr, uid, op['lot_id'][0], ['name', 'ref'], context=context)
                    op['lot_name'] = lots_codes['name'] or ''
                    op['lot_ref'] = lots_codes['ref'] or ''
                    
                product_codes = product_obj.read(cr, uid, op['product_id'][0], ['default_code', 'ean13'], context=context)
                op['default_code'] = product_codes['default_code'] or ''
                op['ean13'] = product_codes['ean13'] or ''
            package_ids = [ x['result_package_id'][0] for x in packs if x.get('result_package_id', False) ]
            if package_ids:
                packages = package_obj.read(cr, uid, package_ids, [], context=context)
                res['packages'] = packages
            
        ul_ids = ul_obj.search(cr, uid, [], context=context)
        if ul_ids:
            uls = ul_obj.read(cr, uid, ul_ids, [], context=context)
            res['uls'] = uls
        
        return res

    def action_pack2(self, cr, uid, picking_ids, operation_ids, qty_done, weight, context=None):
        """ 1) 先修改Operation的已扫描数量(action_drop_down2)
             2) 再调用原来的打包处理程序创建包裹
             3) 修改包裹号为 出货单号 + '_' + 流水号
        """
        op_obj = self.pool.get('stock.pack.operation')
        package_obj = self.pool.get('stock.quant.package')
        for id in operation_ids:
            op_obj.write(cr, uid, id, {'qty_done': qty_done[str(id)] }, context=context)

        package_id = self.action_pack(cr, uid, picking_ids, operation_ids, context=context)
        for picking in self.browse(cr, uid, picking_ids, context=context):
            if picking.pending: 
                raise osv.except_osv(u'警告 !', u'发货单%s已经挂起，不允许出库!' % picking.name)
            # if picking.sale_id:
            #     self.pool['sale.order.logistic'].create(cr, uid, {
            #         'name': 'package',
            #         'user_id': uid,
            #         'order_id': picking.sale_id.id,
            #         'state':'draft',
            #         'memo':u'打包',
            #         })
            pick_name = picking.name
            packages = package_obj.search(cr, uid, [('name', 'like', pick_name)], context=context)
            n = len(packages) + 1
            package_name = "%s%02d" % (pick_name, n)
            package_obj.write(cr, uid, package_id, {'name': package_name, 'weight':weight}, context=context)
        return package_id

    @api.cr_uid_ids_context
    def action_pack(self, cr, uid, picking_ids, operation_filter_ids=None, context=None):
        """ 在系统原有的打包方法中增加一行代码(包裹创建时刻写入 picking_id): 
                package_id = package_obj.create(cr, uid, {'picking_id':picking_id}, context=context)
        """
        if operation_filter_ids == None:
            operation_filter_ids = []
        stock_operation_obj = self.pool.get('stock.pack.operation')
        package_obj = self.pool.get('stock.quant.package')
        stock_move_obj = self.pool.get('stock.move')
        package_id = False
        for picking_id in picking_ids:
            operation_search_domain = [('picking_id', '=', picking_id), ('result_package_id', '=', False)]
            if operation_filter_ids != []:
                operation_search_domain.append(('id', 'in', operation_filter_ids))
            operation_ids = stock_operation_obj.search(cr, uid, operation_search_domain, context=context)
            pack_operation_ids = []
            if operation_ids:
                for operation in stock_operation_obj.browse(cr, uid, operation_ids, context=context):
                    #If we haven't done all qty in operation, we have to split into 2 operation
                    op = operation
                    if (operation.qty_done < operation.product_qty):
                        new_operation = stock_operation_obj.copy(cr, uid, operation.id, {'product_qty': operation.qty_done,'qty_done': operation.qty_done}, context=context)
                        stock_operation_obj.write(cr, uid, operation.id, {'product_qty': operation.product_qty - operation.qty_done,'qty_done': 0, 'lot_id': False}, context=context)
                        op = stock_operation_obj.browse(cr, uid, new_operation, context=context)
                    pack_operation_ids.append(op.id)
                    if op.product_id and op.location_id and op.location_dest_id:
                        stock_move_obj.check_tracking_product(cr, uid, op.product_id, op.lot_id.id, op.location_id, op.location_dest_id, context=context)
                package_id = package_obj.create(cr, uid, {'picking_id': picking_id}, context=context)
                stock_operation_obj.write(cr, uid, pack_operation_ids, {'result_package_id': package_id}, context=context)
        return package_id

    def action_done(self, cr, uid, ids, context=None):
        if not isinstance(ids,list): ids = [ids]
        sale_logistic = self.pool['sale.order.logistic']
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.pending: 
                raise osv.except_osv(u'警告 !', u'发货单%s已经挂起，不允许出库!' % picking.name)
            # if picking.sale_id:
            #     logistic = ''
            #     memo = ''
            #     if picking.picking_type_id.code == 'outgoing':
            #         logistic = 'send'
            #         memo = u'配送中'
            #     if picking.picking_type_id.code == 'internal':
            #         logistic = 'package'
            #         memo = u'打包'
            #     if logistic:
            #         sale_logistic.create(cr, uid, {
            #         'name': logistic,
            #         'user_id': uid,
            #         'order_id': picking.sale_id.id,
            #         'state':'draft',
            #         'memo':memo,
            #         'carrier_id':picking.carrier_id and picking.carrier_id.id or False,
            #         'carrier_no':picking.carrier_tracking_ref,
            #         })
        return super(stock_picking, self).action_done(cr, uid, ids, context=context)

    # @api.cr_uid_ids_context
    # def do_transfer(self, cr, uid, picking_ids, context=None):
    #     res = super(stock_picking, self).do_transfer(cr, uid, picking_ids, context=context)
    #     post_return_picking_id = []
    #     for picking in self.read(cr, uid, picking_ids, ['return_no']):
    #         if picking['return_no']:
    #             post_return_picking_id.append(picking['id'])
    #     if post_return_picking_id:
    #         self.return_details_post(cr, uid, post_return_picking_id, context=context)
    #     return res

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        for pick in self.read(cr, uid, picking, ['pending','name'],context=context):
            if pick['pending']: 
                raise osv.except_osv(u'警告 !', u'发货单%s已经挂起，不允许出库!' % pick['name'])
        return super(stock_picking, self).do_enter_transfer_details(cr, uid, picking, context=context)

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        """
            If no pack operation, we do simple action_done of the picking
            Otherwise, do the pack operations
        """
        if not context:
            context = {}
        stock_move_obj = self.pool.get('stock.move')
        for picking in self.browse(cr, uid, picking_ids, context=context):
            if not picking.pack_operation_ids:
                self.action_done(cr, uid, [picking.id], context=context)
                continue
            else:
                sale_logistic = self.pool['sale.order.logistic']
                need_rereserve, all_op_processed = self.picking_recompute_remaining_quantities(cr, uid, picking, context=context)
                #create extra moves in the picking (unexpected product moves coming from pack operations)
                todo_move_ids = []
                if not all_op_processed:
                    todo_move_ids += self._create_extra_moves(cr, uid, picking, context=context)

                picking.refresh()
                #split move lines eventually

                toassign_move_ids = []
                for move in picking.move_lines:
                    remaining_qty = move.remaining_qty
                    if move.state in ('done', 'cancel'):
                        #ignore stock moves cancelled or already done
                        continue
                    elif move.state == 'draft':
                        toassign_move_ids.append(move.id)
                    if remaining_qty == 0:
                        if move.state in ('draft', 'assigned', 'confirmed'):
                            todo_move_ids.append(move.id)
                    elif remaining_qty > 0 and remaining_qty < move.product_qty:
                        new_move = stock_move_obj.split(cr, uid, move, remaining_qty, context=context)
                        todo_move_ids.append(move.id)
                        #Assign move as it was assigned before
                        toassign_move_ids.append(new_move)
                if need_rereserve or not all_op_processed: 
                    if not picking.location_id.usage in ("supplier", "production", "inventory"):
                        self.rereserve_quants(cr, uid, picking, move_ids=todo_move_ids, context=context)
                    self.do_recompute_remaining_quantities(cr, uid, [picking.id], context=context)
                if todo_move_ids and not context.get('do_only_split'):
                    self.pool.get('stock.move').action_done(cr, uid, todo_move_ids, context=context)
                elif context.get('do_only_split'):
                    context = dict(context, split=todo_move_ids)
                if picking.sale_id and picking.picking_type_code == 'outgoing':
                    sale_logistic.create(cr, uid, {
                        'name': 'send',
                        'user_id': uid,
                        'order_id': picking.sale_id.id,
                        'state':'draft',
                        'memo':u'出库',
                        'carrier_id':picking.carrier_id and picking.carrier_id.id or False,
                        'carrier_no':picking.carrier_tracking_ref,
                        })
            picking.refresh()
            self._create_backorder(cr, uid, picking, context=context)
            if toassign_move_ids:
                stock_move_obj.action_assign(cr, uid, toassign_move_ids, context=context)
        # post_return_picking_id = []
        # for picking in self.read(cr, uid, picking_ids, ['return_no']):
        #     if picking['return_no']:
        #         post_return_picking_id.append(picking['id'])
        # if post_return_picking_id:
        #     self.return_details_post(cr, uid, post_return_picking_id, context=context)
        return True

    def action_print(self, cr, uid, ids, context=None):
        operations = self.browse(cr, uid, ids[0], context=context).pack_operation_ids
        package_ids = [op.result_package_id.id for op in operations if op.result_package_id]
        if not package_ids:
            raise osv.except_osv(u'警告 !', u'该拣货单尚未打包!' )
        package_ids = list(set(package_ids))
        context = dict(context or {}, active_ids=package_ids, active_model='stock.quant.package', active_id=package_ids[0])
        return self.pool.get("report").get_action(cr, uid, package_ids, 'stock.report_package_barcode_small', context=context)

    def return_order(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        sale_model = self.pool['sale.order']
        return_picking_model = self.pool['stock.return.picking']
        return_picking_line_model = self.pool['stock.return.picking.line']
        product_model = self.pool['product.product']

        result = {'result':0,'err_msg':''}
        order_name = vals.get('order_no','')
        sale_id = sale_model.search(cr, uid, [('name','=',order_name)])
        if not sale_id:
            result['result'] = 1
            result['err_msg'] = u'未找到对应的销售单'
            return result
        return_lines = []
        for code in vals.get('return_lines',[]):
            product_id = product_model.search(cr, uid, [('default_code','=',code['product_code']),('active','=',True)])
            if len(product_id) != 1:
                result['result'] = 1
                result['err_msg'] = u'不能识别的产品编号%s'%code['product_code']
                return result
            return_lines.append({'product_id':product_id,'quantity':code['return_qty']})

        sale_order = sale_model.browse(cr, uid, sale_id[0])
        stock_picking_id = sale_order.picking_ids and sale_order.picking_ids[0].id
        ctx = context.copy()
        ctx.update({'active_id':stock_picking_id})
        res = return_picking_model.default_get(cr, uid, ['product_return_moves','move_dest_exists','invoice_state'], context=ctx)
        product_return_moves = []
        for return_lines_details in res['product_return_moves']:
            product_return_moves.append((0,0,return_lines_details))
        res['product_return_moves'] = product_return_moves
        print "=======================res:",res
        return_picking_id = return_picking_model.create(cr, uid, res, context=ctx)

        return_line_ids = []
        return_line_operation = []
        for return_line in return_lines:
            return_line_id = return_picking_line_model.search(cr, uid, [
                ('product_id','=',return_line['product_id']),
                ('wizard_id','=',return_picking_id),
                ('quantity','>=',return_line['quantity'])])
            if return_line_id:
                return_line_ids.append(return_line_id)
                return_line_operation.append([return_line_id,return_line['quantity']])
            else:
                return_line_id1 = return_picking_line_model.search(cr, uid, [
                ('product_id','=',return_line['product_id']),
                ('wizard_id','=',return_picking_id),
                ('quantity','<',return_line['quantity'])])
                operation_qty = return_line['quantity']
                for quantity in return_picking_line_model.read(cr, uid, return_line_id1, ['quantity']):
                    if operation_qty > quantity['quantity']:
                        operation_qty -= quantity['quantity']
                        return_line_ids.append(quantity['id'])
                    else:
                        return_line_ids.append(quantity['id'])
                        return_line_operation.append([quantity['id'],operation_qty])
                        break
        unlink_line_ids = return_picking_line_model.search(cr, uid, [
            ('id','not in',return_line_ids),
            ('wizard_id','=',return_picking_id)])
        for operation in return_line_operation:
            return_picking_line_model.write(cr, uid, operation[0], {'quantity':operation[1]})
        print """""""""""""""""""""""""""""","=================return_picking_id",return_picking_id
        return_picking_line_model.unlink(cr, uid, unlink_line_ids, context=ctx)
        return_dict = return_picking_model.create_returns(cr, uid, [return_picking_id], context=ctx)
        self.write(cr, uid, return_dict['context']['return_picking_id'], {'return_no':vals.get('return_no','')})
        return result

    def return_details_post(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        shop_model = self.pool['ebiz.shop']
        for picking in self.browse(cr, uid, ids, context=context):
            return_dict = {}
            if not picking.return_no or picking.return_send:continue
            return_dict.update({
                    'order_no':picking.sale_id.name,
                    'return_date':picking.date_done,
                    'return_no':picking.return_no,
                    })
            # backorder_id = self.search(cr, uid, [('backorder_id','=',picking.id)])
            # if not backorder_id:
            #     return_dict.update({'diff_lines':[]})
            # else:
            # backorder = self.browse(cr, uid, backorder_id[0])
            diff_lines = []
            for diff_move in picking.move_lines:
                diff_lines.append({
                    'product_code':diff_move.product_id and diff_move.product_id.default_code or '',
                    'return_qty':diff_move.product_uom_qty,
                    })
            return_dict.update({'diff_lines':diff_lines})
            print "===============================%sreturn_dict",return_dict
            shop_model.remote_call(cr, uid, 'return_order',**return_dict)
            picking.write({'return_send':True})
        return True

class stock_pack_operation(osv.osv):
    _inherit = "stock.pack.operation"
    
    def action_drop_down2(self, cr, uid, ids, qty_done, weight=0,context=None):
        print "==================weight",weight
        stock_model = self.pool['stock.picking']
        sale_logistic = self.pool['sale.order.logistic']
        for id in ids:
            self.write(cr, uid, id, {'qty_done': qty_done[str(id)] }, context=context)
        res = self.action_drop_down(cr, uid, ids, context=context)
        sync_picking_ids = []
        picking_weight = []
        for op in self.browse(cr, uid, ids, context=context):
            if not op.picking_id.sale_id:continue
            unprocessed = self.search(cr, uid, [('processed','=','false'),('picking_id','=',op.picking_id.id)])
            if not unprocessed:
                sync_picking_ids.append(op.picking_id.sale_id.id)
            picking_weight.append(op.picking_id)
            #往出运单上写重量 
            # picking = self.pool.get('stock.picking').browse(cr, uid, op.picking_id.id, context=context)
        # if picking_weight:
        #     for pick_weight in set(picking_weight):
        #         if op.picking_id.sale_id:
        #             for picking_id in op.picking_id.sale_id.picking_ids:
        #                 if picking_id.picking_type_code != 'incoming':
        #                     # picking_id.write({'weight':picking_id.weight + float(weight)})
        #                     cr.execute('update stock_picking set weight=%s where id= %s', (picking_id.weight + float(weight), picking_id.id,))
        #         else:
        #             # pick_weight.write({'weight':pick_weight.weight + float(weight)})
        #             cr.execute('update stock_picking set weight=%s where id= %s', (picking_id.weight + float(weight), picking_id.id,))
        #         # cr.execute('update stock_picking set weight=%s where id= %s', (weight, op.picking_id.id,))           
        if sync_picking_ids:
            for sale in set(sync_picking_ids):
                sale_logistic.create(cr, uid, {
                        'name': 'package',
                        'user_id': uid,
                        'order_id': sale,
                        'state':'draft',
                        'memo':u'打包',
                        })
        return res


class stock_picking_wave(osv.osv):
    _inherit = 'stock.picking.wave'

    def list_products(self, cr, uid, context=None):
        ids = self.pool.get('delivery.carrier').search(cr,uid,[('active','=',True)])
        return self.pool.get('delivery.carrier').name_get(cr, uid, ids, context=context)

    def list_partners(self, cr, uid, context=None):
        ids = self.pool.get('res.partner').search(cr,uid,[('name','=','2')])
        return self.pool.get('res.partner').name_get(cr, uid, ids, context=context)

class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'
    
    def create_returns(self, cr, uid, ids, context=None):
        """
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        new_picking_id, pick_type_id = self._create_returns(cr, uid, ids, context=context)
        # Override the context to disable all the potential filters that could have been set previously
        ctx = {
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
            'return_picking_id':new_picking_id,
        }
        return {
            'domain': "[('id', 'in', [" + str(new_picking_id) + "])]",
            'name': _('Returned Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

