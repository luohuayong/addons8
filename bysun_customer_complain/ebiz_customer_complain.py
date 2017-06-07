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

class ebiz_customer_complain(osv.osv):

    _name = "ebiz.customer.complain"
    _inherit = ['mail.thread','ir.needaction_mixin']
    _order = "apply_date desc"
    _description = u"客诉单"

    _columns = {
        'name':fields.char(u'客诉单编号',copy=False),
        'order_id':fields.many2one('sale.order',u'订单编号',required=True),
        'type':fields.selection([('only_refund',u'仅退款'),('return_goods',u'退货退款'),('group_purchase', u'团购')],u'类型'),
        #('make_delivery',u'补发货'),
        'product_id':fields.many2one('product.product',u'产品'),
        'reason':fields.text(u'原因',),
        'description':fields.text(u'说明',),
        
        'return_pay':fields.float(u'需退款金额'),
        'return_amount':fields.float(u'需退货数量'),
        'express_company':fields.many2one('delivery.carrier', u'快递公司'),
        'express_no':fields.char(u'快递单号'),
        'apply_date':fields.datetime(u'申请时间'),
        'state':fields.selection([('draft',u'待审核'),('wait_return_goods',u'退货中'),('quality_failed',u'验货失败'),('over_return_goods',u'已退货'),('wait_refund',u'退款中'),('cancelled',u'已取消'),('rejected',u'拒绝'),('closed',u'关闭')],u'状态'),
        'active':fields.boolean(u'有效'),
        'note': fields.char(u'备注', track_visibility='onchange'),
        'refund_exists': fields.boolean(u'退款单已存在', default=False),
        'return_picking_exists': fields.boolean(u'退货单已存在', default=False),
        'expense_exists': fields.boolean(u'费用单已存在', default=False)
    }

    _sql_constraints = [
        ('default_vehicle_mikey_stock_name_uniq', 'unique (name)', u'名称(name)必须唯一 !')
    ]

    _defaults = {
        'active':True,
        'state': 'draft',
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        type = 'ebiz.customer.complain'
        if not vals.get('name', False):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, type) or '/'
        new_id = super(ebiz_customer_complain, self).create(cr, uid, vals, context=context)
        return new_id 

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for line in self.browse(cr, uid, ids, context=context):     
            result.append((line.id, line.name or ''))
        return result

    def action_rejected(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if (not obj.note):
                raise  osv.except_osv(_(u'警告!'), _(u' "必须填写备注！'))
            if obj.state in ('wait_refund','wait_return_goods','over_return_goods'):
                raise osv.except_osv(_(u'警告!'), _(u' "退款中、退货中、已退货"状态的客诉单不能变更为 "拒绝" ！'))
            obj.write({'state':'rejected'})
        return True

    def action_closed(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.state != 'over_refund':
                raise osv.except_osv(_(u'警告!'), _(u'只有状态是 "已退款" 的客诉单才能变更为 "关闭" ！')) 
            obj.write({'state':'closed'})
        return True 

    def get_new_picking(self, cr, uid, ebiz, picking_type_id, location_id, location_dest_id, group_id, context=None):
        if context is None:
            context = {}
        vals = {}
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'view_picking_form')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        picking_type = self.pool.get('stock.picking.type').browse(cr, uid, picking_type_id)
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('origin','=',ebiz.name),('picking_type_id','=',picking_type_id)])
        #如果已经存在直接跳到picking 的form视图
        if picking_ids:
            return picking_ids,vals,resource_id
        res = []
        product_id = ebiz.product_id and ebiz.product_id.id or False
        bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_tmpl_id', '=', ebiz.product_id.product_tmpl_id.id),('type', '=', 'phantom'), ('active', '=', True)], context=context)
        bom_id = bom_ids and bom_ids[0] or False
        if bom_id:
            bom_product_obj = self.pool.get('mrp.bom').browse(cr, uid, [bom_id], context=context)
            for line in bom_product_obj.bom_line_ids:
                res.append((0,0,{
                    'product_id': line.product_id.id,
                    'name':line.product_id and line.product_id.name or '',
                    'account_id': line.product_id.property_account_income and line.product_id.property_account_income.id or line.product_id.categ_id.property_account_income_categ.id,
                    'product_uom_qty':ebiz.return_amount * line.product_qty,
                    'product_uom': line.product_id.uom_id and line.product_id.uom_id.id or False,
                    'procure_method': 'make_to_stock',
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_expected':time.strftime('%Y-%m-%d %H:%M:%S'),
                    'invoice_state':'none',
                    'state':'draft',
                    'group_id': group_id,
                    }))
        else:
            res.append((0,0,{
                'product_id': product_id,
                'name':ebiz.product_id and ebiz.product_id.name or '',
                'account_id':ebiz.product_id.property_account_income and ebiz.product_id.property_account_income.id or ebiz.product_id.categ_id.property_account_income_categ.id,
                'product_uom_qty':ebiz.return_amount,
                'product_uom': ebiz.product_id.uom_id and ebiz.product_id.uom_id.id or False,
                'procure_method': 'make_to_stock',
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'date_expected':time.strftime('%Y-%m-%d %H:%M:%S'),
                'invoice_state':'none',
                'state':'draft',
                'group_id': group_id,
                }))
        vals.update({
            'picking_type_id':picking_type_id , 
            'partner_id':ebiz.order_id and ebiz.order_id.partner_id.id or False,
            'origin':ebiz.name or '',
            'move_lines': res,
            'carrier_id': ebiz.express_company.id,
            'carrier_tracking_ref': ebiz.express_no,
            })

        return picking_ids,vals,resource_id

    def create_return_picking(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ebiz = self.browse(cr, uid, ids[0], context=context)

        if ebiz.return_amount <= 0:
            raise exceptions.ValidationError(u'退货数量必须大于0!')
        picking_model = self.pool['stock.picking']
        picking_type_id = False
        location_id = False
        location_dest_id = False
        group_id = False
        pack_ids = picking_model.search(cr, uid, [('origin', 'ilike', ebiz.order_id.name)])
        for picking in self.pool.get('stock.picking').browse(cr, uid, pack_ids):
            if picking.picking_type_id.code == 'outgoing':
                picking_type_id = picking.picking_type_id.return_picking_type_id.id
                location_id = picking.picking_type_id.return_picking_type_id.default_location_src_id.id
                location_dest_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                group_id = picking.group_id.id
        picking_ids,vals,resource_id = self.get_new_picking(cr, uid, ebiz, picking_type_id, location_id, location_dest_id, group_id, context=context)
        if picking_ids:
            return {
                    'res_id': picking_ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
            }
        else:
            new_picking = picking_model.create(cr, uid, vals)
            return {
                    'context': context,
                    # 'domain': [('type','=','out_refund')],
                    'view_type': 'form',
                    'res_id': new_picking,
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
            }                       

    def view_return_picking(self, cr, uid, ids, context=None):
        return self.create_return_picking(cr, uid, ids, context=context)

    def create_return_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ebiz = self.browse(cr, uid, ids[0], context=context)
        invoice_model = self.pool['account.invoice']
        vals = {}
        invoice_ids = invoice_model.search(cr, uid, [('origin','=',ebiz.name),('type','=','out_refund')])
        #如果退款单已经存在直接跳到退款单form视图
        if invoice_ids:
            return {
                    'res_id': invoice_ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
            } 
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'invoice_form')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']                  
        res = [] 
        if (ebiz.type == 'return_goods'):
            price_unit = 1
            if ebiz.return_amount:
                price_unit = ebiz.return_pay / ebiz.return_amount
            res.append((0,0,{
                'product_id':ebiz.product_id and ebiz.product_id.id or False,
                'name':ebiz.product_id and ebiz.product_id.name or '',
                'price_unit':price_unit,
                'account_id':ebiz.product_id.property_account_income and ebiz.product_id.property_account_income.id or ebiz.product_id.categ_id.property_account_income_categ.id,
                'quantity':ebiz.return_amount,
                'uos_id': ebiz.product_id.uom_id and ebiz.product_id.uom_id.id or False,
                }))
        else:
            product_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'bysun_customer_complain.ebiz_shop_product_kstk')
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if product_obj:
                res.append((0,0,{
                    'product_id': product_obj.id,
                    'name': product_obj.name,
                    'price_unit': ebiz.return_pay,
                    'account_id': product_obj.property_account_income and product_obj.property_account_income.id or product_obj.categ_id.property_account_income_categ.id,
                    'quantity': 1,
                    'uos_id': product_obj.uom_id and product_obj.uom_id.id or False,
                    }))
        context.update({
            'journal_type': 'sale_refund',
            'type':'out_refund',
            'default_type':'out_refund',
            'default_partner_id':ebiz.order_id and ebiz.order_id.partner_id.id or False,
            })
        default_vals = invoice_model.default_get(cr, uid, ['journal_id'], context=context)
        partner_vals = invoice_model.onchange_partner_id(cr, uid, ids, type='out_refund', \
            partner_id=ebiz.order_id and ebiz.order_id.partner_id.id or False, date_invoice=False, \
            payment_term=False, partner_bank_id=False, company_id=False)['value']
        journal_vals = invoice_model.onchange_journal_id(cr, uid, ids, journal_id=default_vals.get('journal_id',False))['value']
        vals.update(default_vals)
        vals.update(partner_vals)
        vals.update(journal_vals)
        vals.update({
            'type':'out_refund', 
            'partner_id':ebiz.order_id and ebiz.order_id.partner_id.id or False,
            'origin':ebiz.name or '',
            'invoice_line': res,
            })
        _logger.info(vals)
        invoice_id = invoice_model.create(cr, uid, vals, context=context)
        invoice_model.signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        return {
                'context': context,
                'domain': [('type','=','out_refund')],
                'view_type': 'form',
                'view_mode': 'form',
                'res_id':invoice_id,
                'res_model': 'account.invoice',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
        }

    def view_return_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ebiz = self.browse(cr, uid, ids[0], context=context)
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('origin','=',ebiz.name),('type','=','out_refund')])

        if invoice_ids:
            return {
                    'res_id': invoice_ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
            }
        else:
            raise exceptions.ValidationError(u'没有找到退款单!')

    # def create_make_delivery_picking(self, cr, uid, ids, context=None):
    #     # for obj in self.browse(cr, uid, ids, context=context):
    #     #     obj.write({'state':'closed'})
    #     # 补发货单
    #     if context is None:
    #         context = {}
    #     ebiz = self.browse(cr, uid, ids[0], context=context)
    #     picking_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_customer_complain_picking_type_bf')
    #     picking_type_id = picking_type_id and picking_type_id[1] or False
    #     pack_ids = self.pool.get('sale.order').search(cr, uid, [('origin','ilike',ebiz.order_id.name)])
    #     location_id = False
    #     location_dest_id = False
    #     if len(pack_ids) > 1:
    #         for picking in self.pool.get('stock.picking').browse(cr, uid, pack_ids):
    #             for move in picking.move_lines:
    #                 if move.product_id.id == ebiz.product_id.id and picking.picking_type_id.code == 'outgoing':
    #                     location_id = move.location_id.id
    #                 if move.product_id.id == ebiz.product_id.id and picking.picking_type_id.code == 'internal':
    #                     location_dest_id = move.location_dest_id.id
    #     if len(pack_ids) == 1:
    #         picking = self.pool.get('stock.picking').browse(cr, uid, pack_ids[0])
    #         for move in picking.move_lines:
    #             if move.product_id.id == ebiz.product_id.id :
    #                 location_id = move.location_id.id
    #                 location_dest_id = move.location_dest_id.id
    #     picking_ids,context,resource_id = self.get_new_picking(cr, uid, ebiz, picking_type_id, location_id, location_dest_id, context=context)
    #     if picking_ids:
    #         return {
    #                 'res_id': picking_ids[0],
    #                 'view_type': 'form',
    #                 'view_mode': 'form',
    #                 'res_model': 'stock.picking',
    #                 'type': 'ir.actions.act_window',
    #         }
    #     else:
    #         return {
    #                 'context': context,
    #                 # 'domain': [('type','=','out_refund')],
    #                 'view_type': 'form',
    #                 'view_mode': 'form',
    #                 'res_model': 'stock.picking',
    #                 'views': [(resource_id,'form')],
    #                 'type': 'ir.actions.act_window',
    #         }
        
    def create_supplier_account(self, cr, uid, ids, context=None):
        # for obj in self.browse(cr, uid, ids, context=context):
        #     obj.write({'state':'closed'})
        if context is None:
            context = {}
        res = []
        ebiz = self.browse(cr, uid, ids[0], context=context)
        partner = False 
        if not ebiz.product_id.seller_ids:
            raise osv.except_osv(_(u'警告!'), _(u'此产品名没有维护好供应商！'))            
        for line in ebiz.product_id.seller_ids:
            if not partner:  
                partner = line.name
        # partner = ebiz.product_id.supplier_id
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'ebiz_supplier_expence_line_form_view')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id'] 
        supplier_account_ids = self.pool.get('ebiz.supplier.account.line').search(cr, uid, [('origin','=',ebiz.name)])
        if supplier_account_ids:
            return {
                    'res_id': supplier_account_ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'ebiz.supplier.account.line',
                    'type': 'ir.actions.act_window',
            }
        product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gyskk')
        product = False 
        if product_id:
            product_id = product_id[1] 
            product = self.pool.get('product.product').browse(cr, uid, product_id)
        else:
            product_id = ebiz.product_id.id 
            product = ebiz.product_id
        context.update({
            'default_partner_id': partner and partner.id or False,
            'default_origin': ebiz.name,
            'default_type':'cost',
            'default_state': 'draft',
            'default_supplier_mode': partner.supplier_mode,
            'default_sale_id': ebiz.order_id.id,
            'default_product_id': product_id ,
            'default_uom_id': product.uom_id and product.uom_id.id or False,
            'default_notes': ebiz.note,
            'default_amount':-1,
            'default_qty_send': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return {
                'context': context,
                # 'domain': [('type','=','out_refund')],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ebiz.supplier.account.line',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
        }

    def view_supplier_account(self, cr, uid, ids, context=None):
        return self.create_supplier_account(cr, uid, ids, context=context)

    def create_complain(self, cr, uid, complain_info, context=None):
        result = {}
        context = context or {}
        _logger.info(complain_info)

        if complain_info.get('complain_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少客诉单编号参数!'})
            _logger.info(result)
            return result
        else:
            comp_ids = self.search(cr, uid, [('name', '=', complain_info.get('complain_no'))], context=context)
            comp_id = len(comp_ids) and comp_ids[0] or False
            if comp_id:
                result.update({'result': 'failed', 'err_msg': u'客诉单编号已存在!'})
                _logger.info(result)
                return result
        if complain_info.get('order_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少订单编号参数!'})
            _logger.info(result)
            return result
        if complain_info.get('mode', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少客诉类型参数!'})
            _logger.info(result)
            return result
        if (complain_info['mode'] != 0 and complain_info['mode'] != 2 and complain_info['mode'] != 4):
            result.update({'result': 'failed', 'err_msg': u'客诉类型参数不正确!'})
            _logger.info(result)
            return result
        if complain_info.get('reason', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少客诉原因参数!'})
            _logger.info(result)
            return result
        if complain_info.get('description', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少客诉说明参数!'})
            _logger.info(result)
            return result

        if complain_info.get('return_pay', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少退款金额参数!'})
            _logger.info(result)
            return result
        else:
            if complain_info['return_pay'] <= 0:
                result.update({'result': 'failed', 'err_msg': u'退款金额必须大于0!'})
                _logger.info(result)
                return result

        if complain_info.get('apply_date', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少申请时间参数!'})
            _logger.info(result)
            return result

        so_obj = self.pool.get('sale.order')
        so_ids = so_obj.search(cr, uid, [('name', '=', complain_info['order_no'])], context=context)
        so_id = len(so_ids) and so_ids[0] or False
        if not so_id:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编号的订单: %s!'%complain_info['order_no']})
            _logger.info(result)
            return result

        if complain_info.get('product_code', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少产品编码参数!'})
            _logger.info(result)
            return result

        product_obj = self.pool.get('product.product')
        prod_ids = product_obj.search(cr, uid, [('guid', '=', complain_info['product_code'])], context=context)
        prod_id = len(prod_ids) and prod_ids[0] or False
        if not prod_id:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编码的产品: %s!' % complain_info['product_code']})
            _logger.info(result)
            return result

        line_obj = self.pool.get('sale.order.line')
        line_id = line_obj.search(cr, uid, [('order_id', '=', so_id), ('product_id', '=', prod_id)], context=context)
        if not line_id:
            result.update({'result': 'failed', 'err_msg': u'在订单中未找到指定编码的产品: %s!' % complain_info['product_code']})
            _logger.info(result)
            return result
        else:
            #  退货退款: 0   仅退款: 2
            if (complain_info['mode'] == 0):
                if complain_info.get('return_amount', 'failed') == 'failed':
                    result.update({'result': 'failed', 'err_msg': u'缺少退货数量参数!'})
                    _logger.info(result)
                    return result
                # else:
                #     if complain_info.get('return_amount') <= 0:
                #         result.update({'result': 'failed', 'err_msg': u'退货数量必须大于0!'})
                #         _logger.info(result)
                #         return result
                for line_obj in line_obj.browse(cr, uid, line_id, context=context):
                    if line_obj['product_uom_qty'] < complain_info['return_amount']:
                        result.update({'result': 'failed', 'err_msg': u'退货数量不能大于原订单的数量!'})
                        _logger.info(result)
                        return result

        typestr = ''
        if (complain_info['mode'] == 0):
            typestr = 'return_goods'
        elif (complain_info['mode'] == 2):
            typestr = 'only_refund'
        elif (complain_info['mode'] == 4):
            typestr = 'group_purchase'

        apply_date = complain_info.get('apply_date', fields.datetime.now())
        apply_date = datetime.datetime.strptime(apply_date,"%Y/%m/%d %H:%M:%S")
        apply_date = apply_date - datetime.timedelta(hours=8)

        complain_vals = {
            'name': complain_info['complain_no'],
            'order_id': so_id,
            'type': typestr,
            'product_id': prod_id,
            'reason': complain_info['reason'],
            'description': complain_info['description'],
            'return_pay': complain_info['return_pay'],
            'return_amount': complain_info['return_amount'],
            'apply_date': apply_date,
            'state': 'draft',
            'active': True,
        }

        so = so_obj.browse(cr, uid, so_id, context=context)
        if so and so.state not in  ['cancel'] and not so.shipped and not so.pending:
            so.action_suspend()

        self.create(cr, uid, complain_vals, context=context)
        result.update({'result': 'success', 'err_msg': ''})
        return result

    def sync_complain_from_shop(self, cr, uid, vals, context=None):
        complain_vals = {
            'complain_no': 'bbbbbc',
            'order_no': 'SO20160511007',
            'mode': 0,
            'product_code': '103113',
            'reason': 'dafas',
            'description': 'dafsd',
            'return_pay': 10.0,
            'return_amount': 1,
            'apply_date': '2016/05/12 10:20:03',
        }
        result = self.create_complain(cr, uid, complain_vals, context= context)
        _logger.info(result)
        return result

    def update_complain(self, cr, uid, complain_info, context=None):
        result = {}
        context = context or {}
        _logger.info(complain_info)

        if complain_info.get('complain_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少客诉单编号参数!'})
            _logger.info(result)
            return result


        if complain_info.get('status', 'failed') == 'failed':
            if complain_info.get('express_company', 'failed') == 'failed':
                result.update({'result': 'failed', 'err_msg': u'缺少快递公司参数!'})
                _logger.info(result)
                return result
            else:
                carrier_obj = self.pool.get('delivery.carrier')
                carrier_ids = carrier_obj.search(cr, uid, [('name', '=', complain_info.get('express_company'))], context=context)
                if not carrier_ids:
                    result.update({'result': 'failed', 'err_msg': (u'快递公司 %s 不正确，请保证商城的快递公司信息和ERP一致！')%complain_info.get('express_company')})
                    _logger.info(result)
                    return result
                carrier_id = carrier_ids and carrier_ids[0] or False

            if complain_info.get('express_no', 'failed') == 'failed':
                result.update({'result': 'failed', 'err_msg': u'缺少快递单号参数!'})
                _logger.info(result)
                return result

        cp_obj = self.pool.get('ebiz.customer.complain')
        cp_ids = self.search(cr, uid, [('name', '=', complain_info['complain_no'])], context=context)
        cp_id = len(cp_ids) and cp_ids[0] or False
        if not cp_id:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编号的客诉单: %s!'%complain_info['complain_no']})
            _logger.info(result)
            return result

        if complain_info.get('status', 'failed') == 'cancel':
            cp_obj = self.browse(cr, uid, cp_ids, context=context)
            if cp_obj:
                if (cp_obj.express_company):
                    result.update({'result': 'failed', 'err_msg': u'买家已发货，不允许取消!'})
                    _logger.info(result)
                    return result
                picking_ids = self.pool.get('stock.picking').search(cr, uid, [('origin', '=', cp_obj.name)], context=context)
                picking_obj = self.pool.get('stock.picking').browse(cr, uid, picking_ids, context=context)
                if picking_obj:
                    picking_obj.action_cancel()
                cp_obj.write({'state': 'cancelled'})

                # so_ids = self.pool.get('sale.order').search(cr, uid, [('name', '=', cp_obj.order_id.id)], context=context)
                # so_obj = self.pool.get('sale.order').browse(cr, uid, so_ids and so_ids[0] or False, context=context)
                if cp_obj.order_id.pending:
                    cp_obj.order_id.action_suspend()
                result.update({'result': 'success', 'err_msg': ''})
                return result

        complain_vals = {
            'express_company': carrier_id,
            'express_no': complain_info['express_no'],
        }
        cp_obj.write(cr, uid, cp_ids[0], complain_vals, context=context)

        picking_obj = self.pool.get('stock.picking')
        picking_ids = picking_obj.search(cr, uid, [('origin', '=', complain_info['complain_no'])], context=context)
        picking_vals = {
            'carrier_id': carrier_id,
            'carrier_tracking_ref': complain_info['express_no']
        }
        for picking_obj in picking_obj.browse(cr, uid, picking_ids, context = context):
            picking_obj.write(picking_vals)

        result.update({'result': 'success', 'err_msg': ''})
        return result

    def sync_return_goods_from_shop(self, cr, uid, vals, context=None):
        complain_vals = {
            'complain_no': 'bbbbbc',
            'express_company': '圆通速递',
            'express_no': 'afdaseweeeee'
        }
        result = self.update_complain(cr, uid, complain_vals, context= context)
        _logger.info(result)
        return result

    def _prepare_sync_complain_vals(self, cr, uid, obj, vals, context=None):

        mode = '0'
        if (obj.type == 'only_refund'):
            mode = '2'
        elif (obj.type == 'group_purchase'):
            mode = '4'

        changing = {
            'complain_no': obj.name,
            'mode': mode,
            'return_pay': obj.return_pay,
            'return_amount': int(obj.return_amount),
            'memo': obj.note and obj.note or '',
        }

        if vals.get('return_pay', -1) != -1:
            changing.update({'return_pay': vals.get('return_pay')})

        if vals.get('return_amount', -1) != -1:
            changing.update({'return_amount': int(vals.get('return_amount'))})

        if vals.get('note', 'failed') != 'failed':
            changing.update({'memo': vals.get('note')})

        return changing

    def _update_complain(self, cr, uid, ids, vals, context=None):
        _logger.info("syncing complain changing")
        shop_obj = self.pool.get('ebiz.shop')
        result = {}
        # now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in self.browse(cr, uid, ids, context=context):
            post_vals = self._prepare_sync_complain_vals(cr, uid, p, vals, context=context)
            res = shop_obj.remote_call(cr, uid, 'complain', 'complainsync', **post_vals)
            if res.get('result','') != 'success':
                result.update({p:res.get('err_msg','')})
        if result:
            err_msg = ''
            for err in result:
                err_msg += '%s:%s\n'%(err.name_get()[0][1],result.get(err))
            raise exceptions.ValidationError(err_msg)
        return result


    def _prepare_sync_complain_status_vals(self, cr, uid, obj, vals, context=None):
        default_return_goods_address = ''
        default_recipients = ''
        default_tel = ''
        if obj.product_id and obj.product_id.seller_id:
            partner_obj = self.pool.get('res.partner').browse(cr, uid, obj.product_id.seller_id.id, context=context)
            if partner_obj and partner_obj.supplier_mode not in ['Direct_Procurement','Consign_stock_in']:
                default_return_goods_address = partner_obj.default_return_goods_address
                default_recipients = partner_obj.default_recipients
                default_tel = partner_obj.default_recipients_phone
            elif partner_obj and partner_obj.stock_warehouse_id and partner_obj.stock_warehouse_id.partner_id:
                default_return_goods_address = partner_obj.stock_warehouse_id.partner_id.default_return_goods_address
                default_recipients = partner_obj.stock_warehouse_id.partner_id.default_recipients
                default_tel = partner_obj.stock_warehouse_id.partner_id.default_recipients_phone
        else:
            raise exceptions.ValidationError(u'该客诉单没有产品信息或没有配置产品的供应商！')

        changing = {
            'complain_no': obj.name,
            'status': vals.get('state'),
            'default_return_goods_address': default_return_goods_address,
            'default_recipients': default_recipients,
            'default_tel': default_tel,
            'memo': obj.note and obj.note or '',
        }
        return changing

    def _update_complain_status(self, cr, uid, ids, vals, context=None):
        _logger.info("syncing complain changing")
        shop_obj = self.pool.get('ebiz.shop')
        result = {}
        for p in self.browse(cr, uid, ids, context=context):
            post_vals = self._prepare_sync_complain_status_vals(cr, uid, p, vals, context=context)
            res = shop_obj.remote_call(cr, uid, 'complain', 'complainstatesync', **post_vals)
            if res.get('result','') != 'success':
                result.update({p:res.get('err_msg','')})
        if result:
            err_msg = ''
            for err in result:
                err_msg += '%s:%s\n'%(err.name_get()[0][1],result.get(err))
            raise exceptions.ValidationError(err_msg)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        result = super(ebiz_customer_complain, self).write(cr, uid, ids, vals, context=context)
        if not context.get('no_send',False):
            if vals.get('state','failed') != 'failed' and vals.get('state') not in ['draft','quality_failed','over_return_goods','cancelled']:
                self._update_complain_status(cr, uid, ids, vals, context=context)
            if vals.get('return_pay', 0) != 0 or vals.get('return_amount', 0) != 0 or vals.get('note', 'failed') != 'failed':
                self._update_complain(cr, uid, ids, vals, context=context)
        return result

ebiz_customer_complain()

#
# class ebiz_customer_complain_status(osv.osv):
#     _name = 'ebiz.customer.complain.status'
#
#     _columns = {
#         'name': fields.char('客诉单状态', required=True),
#         ''
#         # Statistics for the kanban view
#         'last_done_picking': fields.function(_get_tristate_values,
#             type='char',
#             string='Last 10 Done Pickings'),
#
#         'count_picking_draft': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'count_picking_ready': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'count_picking': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'count_picking_waiting': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'count_picking_late': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'count_picking_backorders': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#
#         'rate_picking_late': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#         'rate_picking_backorders': fields.function(_get_picking_count,
#             type='integer', multi='_get_picking_count'),
#
#     }
#
