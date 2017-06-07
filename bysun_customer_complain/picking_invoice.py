# -*- encoding: utf-8 -*-

import logging
import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.osv import fields, osv, expression
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp import workflow 
from openerp import models, api
import re

class stock_picking(osv.osv):

    _inherit = "stock.picking"

    # _columns = {
    #     'supplier_id':fields.many2one('res.partner',u'供应商'),
    # }

    def create(self, cr, uid, default, context=None):
        customer_complain = self.pool.get('ebiz.customer.complain')
        if default.get('origin',False):
            complain_ids = customer_complain.search(cr, uid, [('name','=',default.get('origin',False))],)
            if complain_ids:
                for complain in customer_complain.browse(cr, uid, complain_ids):
                    if complain.type == 'return_goods' and complain.state != 'wait_return_goods' and not complain.return_picking_exists:
                        complain.write({'state': 'wait_return_goods','return_picking_exists': True})
        return super(stock_picking, self).create(cr, uid, default, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        comp_obj = self.pool.get('ebiz.customer.complain')
        for picking in self.browse(cr, uid, ids, context=context):
            comp_ids = comp_obj.search(cr, uid, [('name', '=', picking.origin)], context=context)
            comp_id = len(comp_ids) and comp_ids[0] or False
            comp = comp_obj.browse(cr, uid, comp_id)
            if comp_id and not picking.backorder_id:
                comp.write({'state': 'quality_failed'})
                ctx = context.copy()
                ctx.update({'no_send':True})
                comp_obj.write(cr, uid, [comp_id], {'note':''}, context=ctx)

        return super(stock_picking, self).action_cancel(cr, uid, ids, context=context)

stock_picking()

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details' 

    @api.one
    def do_detailed_transfer(self):
        res = super(stock_transfer_details, self).do_detailed_transfer()
        complains = self.env['ebiz.customer.complain'].search([('name','=',self.picking_id.origin)])
        if complains:
            complains.write({'state':'over_return_goods'})
        return res
           
stock_transfer_details()

class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def create(self, cr, uid, default, context=None):
        customer_complain = self.pool.get('ebiz.customer.complain')
        if default.get('origin',False):
            complain_ids = customer_complain.search(cr, uid, [('name','=',default.get('origin',False))],)
            if complain_ids:
                for complain in customer_complain.browse(cr, uid, complain_ids):
                    if complain.type in ('return_goods','only_refund'):
                        complain.write({'state': 'wait_refund', 'refund_exists': True})
        return super(account_invoice, self).create(cr, uid, default, context=context)

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        result = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
        inv = self.browse(cr, uid, ids[0], context=context)
        comp_ids = self.pool.get('ebiz.customer.complain').search(cr, uid, [('name', '=', inv.origin)], context=context)
        comp_obj = self.pool.get('ebiz.customer.complain').browse(cr, uid, comp_ids, context=context)
        if comp_obj:
            so_obj = self.pool.get('sale.order').browse(cr, uid, [comp_obj.order_id.id], context=context)
            if so_obj:
                result['context'].update({'default_journal_id': so_obj.journal_id.id})
                result['context'].update({
                    'default_sale_payment_ref': so_obj.payment_lines and so_obj.payment_lines[0] and so_obj.payment_lines[0].ref or '',
                    'default_sale_order_id':so_obj.id,
                    })
        return result

account_invoice()

class account_voucher(osv.osv):

    _inherit = "account.voucher"

    _columns = {
        'sale_payment_ref':fields.char(u'相关销售支付单号'),
        'sale_order_id':fields.many2one('sale.order',u'相关销售订单')
    }

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        self.signal_workflow(cr, uid, ids, 'proforma_voucher')

        for invoice in self.pool.get('account.invoice').browse(cr, uid, context.get('active_ids', []), context=context):
            complain_ids = self.pool.get('ebiz.customer.complain').search(cr, uid, [('name', '=', invoice.origin)],)

            if complain_ids:
                self.pool.get('ebiz.customer.complain').write(cr, uid, complain_ids, {'state':'closed'}, context=context)


        return {'type': 'ir.actions.act_window_close'}
    #
    # def proforma_voucher(self, cr, uid, ids, context=None):
    #     self.action_move_line_create(cr, uid, ids, context=context)
    #     for voucher in self.browse(cr, uid, ids, context=context):
    #         invoice = False
    #         for line in voucher.line_dr_ids:
    #             if not invoice and line.reconcile:
    #                 invoice = line.move_line_id.invoice
    #         if invoice:
    #             complain_ids = self.pool.get('ebiz.customer.complain').search(cr, uid, [('name','=',invoice.origin)],)
    #             if complain_ids:
    #                 for complain in self.pool.get('ebiz.customer.complain').browse(cr, uid, complain_ids):
    #                     complain.write({'state':'closed'})
    #     return True

account_voucher()