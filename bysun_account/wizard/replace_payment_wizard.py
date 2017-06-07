# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class replace_payment_line(models.TransientModel):
    _name = 'ebiz.account.replace.payment.line'

    journal_id = fields.Many2one('account.journal', u'支付方式', required=True, domain=['&', ('type', 'in', ['cash', 'bank']), ('code', '!=', 'COD')])
    amount = fields.Float(u'支付金额', required=True)
    ref = fields.Char(u'支付单号', required=True, copy=False)
    pay_time = fields.Datetime(u'支付时间', required=True, default=lambda self: fields.Datetime.now())
    wizard_id = fields.Many2one('ebiz.account.replace_payment.wizard', u'替换支付方式')


class replace_payment_wizard(models.TransientModel):
    _name = 'ebiz.account.replace_payment.wizard'

    payment_lines = fields.One2many('ebiz.account.replace.payment.line', 'wizard_id', u'支付方式')

    def cusotmer_sign(self, cr, uid, ids, context=None):
        so_obj = self.pool.get('sale.order')
        data = self.browse(cr, uid, ids[0], context=context)
        sale_id = context.get('active_id', False)

        if data.payment_lines:
            payment_lines = [{'journal_id': l.journal_id.id, 'amount': l.amount, 'ref': l.ref, 'pay_time': l.pay_time} for l in data.payment_lines]
            so_obj.replace_payment(cr, uid, [sale_id], payment_lines, context=context)

        so_obj.customer_sign(cr, uid, [sale_id], context=context)

        return {'type': 'ir.actions.act_window_close'}
