# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import logging
import datetime
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        complain_ids = self.env['ebiz.customer.complain'].search([('name', '=', self.origin)])
        complain_ids.write({'state':'closed'})
        return self.write({'state': 'paid'})

    @api.multi
    @api.depends('origin')
    def _get_payref(self):
        _logger.info('------------begin--------')
        for invoice_object in self:
            complain_name = invoice_object.origin
            _logger.info(complain_name)
            if complain_name:
                complain_obj = self.env['ebiz.customer.complain']
                complain = complain_obj.search([('name','=',complain_name)])
                if complain:
                    invoice_object.payref =complain.order_id.payment_lines.ref
                else:
                    sale_obj = self.env['sale.order']
                    sale = sale_obj.search([('name','=',complain_name)])
                    invoice_object.payref = sale.payment_lines.ref
        _logger.info('------------end--------')

    def _search_payref(self, cr, uid, obj, name, domain, context):
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in ('payref'), 'Invalid domain left operand'
            assert operator in ('=', '!=', 'ilike'), 'Invalid domain operator'
            assert isinstance(value, str), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            ids = []
            if name == 'payref':
                invoice_ids = self.search(cr, uid, [], context=context)
                if invoice_ids:
                    #TODO: Still optimization possible when searching virtual quantities
                    for element in self.browse(cr, uid, invoice_ids, context=context):
                        if eval(str(element[field]) + operator + str(value)):
                            ids.append(element.id)
                    res.append(('id', 'in', ids))
            else:
                pass
        return res

    payref = fields.Char(compute="_get_payref", string= u'支付流水号', fnct_search=_search_payref)

    @api.multi
    def return_invoice_check(self):
        for invoice in self:
            if self.journal_id.code == 'SCNJ':
                complains = self.env['ebiz.customer.complain'].search([('name','=',self.origin)])
                if not complains:return True
                invoices = self.search([('journal_id.code','=','SAJ'),('origin','=',complains.order_id.name)])
                if not invoices or invoices.state == 'cancel':
                    if invoice.invoice_line.product_id.default_code != 'kstk' or invoice.invoice_line.account_id.code != '2206':
                        raise ValidationError(u'发票对应的收入发票已取消或未产生，请更改此发票的科目为 [2206]预收账款退款:%s'%(invoice.origin))
        return True


class sale_order(models.Model):
    _inherit = 'sale.order'

    def buyer_sign(self, cr, uid, sign_info, context=None):
        result = {}
        context = context or {}
        _logger.info(sign_info)

        if sign_info.get('order_no', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少订单编号参数!'})
            _logger.info(result)
            return result
        if sign_info.get('sign_date', 'failed') == 'failed':
            result.update({'result': 'failed', 'err_msg': u'缺少签收时间参数!'})
            _logger.info(result)
            return result

        so_ids = self.search(cr, uid, [('name', '=', sign_info['order_no'])], context=context)
        so_id = len(so_ids) and so_ids[0] or False
        if not so_id:
            result.update({'result': 'failed', 'err_msg': u'未找到指定编号的订单: %s!'%sign_info['order_no']})
            _logger.info(result)
            return result

        so = self.browse(cr, uid, so_id, context=context)
        if (so and so.sign_date):
            result.update({'result': 'failed', 'err_msg': u'指定编号的订单: %s 已签收!'%sign_info['order_no']})
            _logger.info(result)
            return result

        if (so and so.state in ('draft','sent','cancel')):
            result.update({'result': 'failed', 'err_msg': u'指定编号的订单状态未审核!'})
            _logger.info(result)
            return result

        sign_date = sign_info.get('sign_date', fields.Datetime.now())
        sign_date = datetime.datetime.strptime(sign_date,"%Y/%m/%d %H:%M:%S")
        sign_date = sign_date - datetime.timedelta(hours=8)

        self.write(cr, uid, [so_id], {'sign_date': '%s'%sign_date}, context=context)
        result.update({'result': 'success', 'err_msg': ''})
        # self.customer_sign(cr, uid, [so_id], context=context)
        return result

    def customer_sign(self, cr, uid, ids, context=None):
        """客户签收"""
        context = dict(context or {})
        invoice_obj = self.pool.get('account.invoice')
        voucher_obj = self.pool.get('account.voucher')

        sale_id = ids and ids[0] or False
        sale = self.browse(cr, uid, sale_id, context=context)
        if sale.amount_total == 0:
            _logger.warn(u'订单总金额为0，不创建发票，也不生成付款单.')
            return True

        # 创建发票
        self.manual_invoice(cr, uid, [sale_id], context=context)

        # 确认发票
        # invoice_ids = self.read(cr, uid, sale_id, ['invoice_ids'], context=context)['invoice_ids']
        # invoice_obj.signal_workflow(cr, uid, invoice_ids, 'invoice_open', context=context)
        # invoice = invoice_obj.browse(cr, uid, invoice_ids[0], context=context)
        # move_line_ids = [l.id for l in invoice.move_id.line_id if l.account_id.type in ('payable', 'receivable')]
        # context.update({'invoice_id': invoice.id, 'move_line_ids': move_line_ids})
        # # 创建付款单
        # sale = self.browse(cr, uid, sale_id, context)
        # for line in sale.payment_lines:
        #     val = {'partner_id': sale.partner_id.id, 'amount': line.amount, 'journal_id': line.journal_id.id, 'type': 'receipt', 'reference': line.ref, 'company_id': sale.company_id.id}
        #     # data = voucher_obj.basic_onchange_partner(cr, uid, False, val['partner_id'], val['journal_id'], 'sale')
        #     data = voucher_obj \
        #         .onchange_partner_id(cr, uid, False, val['partner_id'], val['journal_id'], val['amount'], False, val['type'], False, context=context)

        #     val.update(data['value'], reference=line.ref)
        #     val['line_cr_ids'] = [(0, 0, l) for l in val['line_cr_ids'] if l['move_line_id'] in move_line_ids] or False
        #     val['line_dr_ids'] = [(0, 0, l) for l in val['line_dr_ids'] if l['move_line_id'] in move_line_ids] or False

        #     voucher_obj.create(cr, uid, val, context=context)

        # picking_id = context and context.get('picking_id')
        # if picking_id:
        #     sale_logistic = self.pool['sale.order.logistic']
        #     sl_vals = {'name': 'signed', 'user_id': uid, 'order_id': ids[0], 'state': 'draft', 'memo':u'客户签收'}
        #     sale_logistic.create(cr, uid, sl_vals, context=context)

        #     picking_obj = self.pool.get('stock.picking')
        #     picking_obj.write(cr, uid, [picking_id], {'customer_signed': True}, context=context)

        return True

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        self.customer_sign(cr, uid, ids, context=context)
        return res

class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    bank_statement_type = fields.Selection([('refund',u'退款对账'),('receive',u'收入对账')], u'对账类型')

    @api.multi
    def auto_reconcile_bank_statement(self):
        for bank_statement in self:
            for bank_line in bank_statement.line_ids:
                bank_line.auto_reconcile_bank_statement()
        return True

class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.multi
    def auto_reconcile_bank_statement(self):
        invoice_model = self.env['account.invoice']
        sale_model = self.env['sale.order']
        for bank_line in self:
            if bank_line.journal_entry_id:
                continue
            sales = sale_model.search([('payment_lines.payorderosn','ilike',bank_line.ref + '%'),('payment_lines.ref','=',bank_line.name),('state','!=','cancel')])
            invoice_origins = [sale.name for sale in sales] or ['error']
            invoices = invoice_model.search([('partner_id','=',bank_line.partner_id.id),('origin','in',invoice_origins),\
                ('state','not in',['cancel','paid'])])
            if not invoices:
                _logger.info(u"未找到对应的客户发票:%s"%((bank_line.ref or '') + ':' + (bank_line.name or '')))
                continue
            else:
                amount = 0.00
                for invoice in invoices:
                    amount += invoice.amount_total
                if abs(amount - bank_line.amount) > 0.00001:
                    _logger.info(u"银行付款单金额与发票金额不等:%s"%((bank_line.ref or '') + ':' + (bank_line.name or '')))
                    continue
                else:
                    invoices.signal_workflow('invoice_open')
                    reconcile_list = []
                    for invoice2 in invoices:
                        for move_line in invoice2.move_id.line_id:
                            if (move_line.debit > 0) and (move_line.account_id.code == '1122'):
                                reconcile_list += [{
                                    'credit':move_line.debit,
                                    'debit':move_line.credit,
                                    'name':move_line.name,
                                    'counterpart_move_line_id':move_line.id,
                                }]
                    bank_line.process_reconciliation(reconcile_list)
        return True


