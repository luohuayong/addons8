# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class sale_payment_line(models.Model):
    _name = 'sale.payment.line'
    _description = '支付明细'

    order_id = fields.Many2one('sale.order', u'订单')
    journal_id = fields.Many2one('account.journal', u'支付方式', domain=[('type', 'in', ['cash', 'bank'])])
    amount = fields.Float(u'支付金额')
    ref = fields.Char(u'支付单号', copy=False)
    pay_time = fields.Datetime(u'支付时间')

class sale_order(models.Model):
    _inherit = 'sale.order'

    fapiao = fields.Boolean(string=u"要发票", copy=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    fp_text = fields.Char(u'开票内容', copy=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    payment_lines = fields.One2many('sale.payment.line', 'order_id', string=u'订单支付明细', )

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """增加是否要开票的信息 """
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        if order.fapiao:
            invoice_vals.update({'fapiao': order.fapiao, 'fp_text': order.fp_text})
        return invoice_vals

    def prepare_customer_sign(self, cr, uid, ids, context=None):
        """弹出客户签收的wizard, 判断是否有货到付款的支付方式"""
        dataobj = self.pool.get('ir.model.data')
        cod_id = dataobj.xmlid_to_res_id(cr, uid, 'ebiz_account.journal_cash_on_delivery')

        sale_id = ids and ids[0] or False
        order = self.browse(cr, uid, sale_id, context=context)
        # cod_line = next((line for line in order.payment_lines if line.journal_id.id == cod_id), None)
        cod_line = order.is_cod or False

        if not cod_line:
            context.update({'hide_payment_lines': True})

        dummy, view_id = dataobj.get_object_reference(cr, uid, 'ebiz_account', 'view_replace_payment_wizard_form')
        res = {
            "name": u'客户签收',
            "type": "ir.actions.act_window",
            "res_model": "ebiz.account.replace_payment.wizard",
            'view_mode': 'form',
            "view_id": view_id,
            'target': "new",
            "context": context,
        }
        return res

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
        invoice_ids = self.read(cr, uid, sale_id, ['invoice_ids'], context=context)['invoice_ids']
        invoice_obj.signal_workflow(cr, uid, invoice_ids, 'invoice_open', context=context)
        invoice = invoice_obj.browse(cr, uid, invoice_ids[0], context=context)
        move_line_ids = [l.id for l in invoice.move_id.line_id if l.account_id.type in ('payable', 'receivable')]
        context.update({'invoice_id': invoice.id, 'move_line_ids': move_line_ids})
        # 创建付款单
        sale = self.browse(cr, uid, sale_id, context)
        for line in sale.payment_lines:
            val = {'partner_id': sale.partner_id.id, 'amount': line.amount, 'journal_id': line.journal_id.id, 'type': 'receipt', 'reference': line.ref, 'company_id': sale.company_id.id}
            # data = voucher_obj.basic_onchange_partner(cr, uid, False, val['partner_id'], val['journal_id'], 'sale')
            data = voucher_obj \
                .onchange_partner_id(cr, uid, False, val['partner_id'], val['journal_id'], val['amount'], False, val['type'], False, context=context)

            val.update(data['value'], reference=line.ref)
            val['line_cr_ids'] = [(0, 0, l) for l in val['line_cr_ids'] if l['move_line_id'] in move_line_ids] or False
            val['line_dr_ids'] = [(0, 0, l) for l in val['line_dr_ids'] if l['move_line_id'] in move_line_ids] or False

            voucher_obj.create(cr, uid, val, context=context)

        return True

    def cod_pay_back(self, cr, uid, order_no, payment_lines,context=None):
        send_val = {}
        payment_list = []
        journal_model = self.pool['account.journal']
        shop_model = self.pool['ebiz.shop']
        for payment_line in payment_lines:
            payment_method = journal_model.read(cr, uid, payment_line['journal_id'], ['website_code'])
            payment_list.append({
                'serial_no':payment_line['ref'],
                'payment_method':payment_method['website_code'],
                'amount':payment_line['amount'],
                'pay_date':payment_line['pay_time'],
                })
        send_val.update({
                'payment_lines':payment_list,
                'order_no':order_no,
            })
        _logger.info(send_val)
        result = shop_model.remote_call(cr, uid, 'pay_back', **send_val)
        return result

    def replace_payment(self, cr, uid, ids, payment_lines, context=None):
        """替换货到付款明细行"""
        dataobj = self.pool.get('ir.model.data')
        cod_id = dataobj.xmlid_to_res_id(cr, uid, 'ebiz_account.journal_cash_on_delivery')

        sale_id = ids and ids[0] or False
        order = self.browse(cr, uid, sale_id, context=context)
        if not order.payment_lines:
            raise exceptions.ValidationError(u'该订单没有付款明细！')

        cod_line = next((line for line in order.payment_lines if line.journal_id.id == cod_id), None)
        if not cod_line:
            raise exceptions.ValidationError(u'没有货到付款情况！')

        total_amount = sum(l['amount'] for l in payment_lines)
        if total_amount != cod_line.amount:
            raise exceptions.ValidationError(u'金额不一致，不可替换！')

        # 同步货到付款明细
        result = self.cod_pay_back(cr, uid, order.name, payment_lines, context=context)
        if not result or not result.get('result',1) != 0:
            raise exceptions.ValidationError(u'同步货到付款明细失败,请稍候重试')

        # 替换货到付款明细行
        lines = [(0, 0, line) for line in payment_lines]
        lines.append((2, cod_line.id, 0))
        self.write(cr, uid, ids, {'payment_lines': lines}, context=context)

        return True


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """"计算优惠减款"""
        line = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
        if context.get('discount_amount', None):
            discount_amount = context['discount_amount']
            total_amount = context['total_amount']
            price_unit = line['price_unit']
            price_unit = price_unit - discount_amount * price_unit / total_amount
            price_unit = round(price_unit, self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            line['price_unit'] = price_unit
        return line

    def invoice_line_create(self, cr, uid, ids, context=None):
        """"计算优惠减款"""
        if not context:
            context = {}

        dataobj = self.pool.get('ir.model.data')
        discount_pid = dataobj.xmlid_to_res_id(cr, uid, 'ebiz_stock.ebiz_shop_product_yhjk')

        # lines = self.browse(cr, uid, ids, context=context)
        lines = self.read(cr, uid, ids, ['product_id', 'price_subtotal', 'price_unit', 'product_uos_qty'], context=context)
        discount_order_lines = [l for l in lines if l['product_id'][0] == discount_pid]
        if discount_order_lines:
            discount_ids = [x['id'] for x in discount_order_lines]
            ids = list(set(ids) - set(discount_ids))

            discount_amount = -sum(l['price_unit'] * l['product_uos_qty'] for l in discount_order_lines)
            total_amount = sum(l['price_unit'] * l['product_uos_qty'] for l in lines if l['product_id'][0] != discount_pid)
            context.update({'discount_amount': discount_amount, 'total_amount': total_amount})

        inv_ids = super(sale_order_line, self).invoice_line_create(cr, uid, ids, context=context)

        # 尾差调整
        if inv_ids and discount_order_lines:
            inv_line_obj = self.pool.get('account.invoice.line')
            inv_line = inv_line_obj.browse(cr, uid, inv_ids[0], context=context)
            invoice_amount = inv_line.invoice_id.amount_total
            sale_amount = context['total_amount']
            if invoice_amount != sale_amount:
                diff = sale_amount - invoice_amount
                self.adjust_sale_invoice_amount(cr, uid, inv_line.invoice_id.id, diff, context)

        return inv_ids

    def adjust_sale_invoice_amount(self, cr, uid, invoice_id, diff, context):
        dataobj = self.pool.get('ir.model.data')
        inv_line_obj = self.pool.get('account.invoice.line')
        wctz_prod = dataobj.xmlid_to_object(cr, uid, 'ebiz_account.ebiz_shop_product_wctz', True, context=context)
        account = wctz_prod.property_account_expense
        if not account:
            raise exceptions.ValidationError(u'产品[尾差调整]需要设置费用科目!')
        data = {
            'invoice_id': invoice_id,
            'product_id': wctz_prod.id,
            'name': wctz_prod.name,
            'account_id': account.id,
            'quantity': 1,
            'price_unit': diff
        }
        inv_line_id = inv_line_obj.create(cr, uid, data, context=context)
        return inv_line_id
