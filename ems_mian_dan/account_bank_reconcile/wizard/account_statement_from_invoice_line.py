# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv

class account_statement_from_invoice_lines(osv.osv_memory):
    """
    Generate Entries by Statement from Invoices
    """
    _inherit = "account.statement.from.invoice.lines"

    _columns = {
        'bank_id':fields.many2one('account.bank.statement',u'银行对账单'),
    }

    _defaults = {
        'bank_id':lambda s,c,u,context=None:context.get('active_id',False),
    }

    def onchange_bank_id(self, cr, uid, ids, bank_id, context=None):
        domain = [('account_id.type','in',['receivable','payable']),('reconcile_id','=',False),\
        ('reconcile_partial_id','=',False), ('state', '=', 'valid')]
        res = {'domain':{'line_ids':[]}}
        if not bank_id:
            res['domain']['line_ids'] = domain
        else:
            bank = self.pool['account.bank.statement'].browse(cr, uid, bank_id, context=context)
            if bank.journal_id.code == 'appal':
                #cr.execute("""select
                #    id from account_invoice
                #    where origin in
                #    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where ref ilike '2%'))""")
                cr.execute("""select
                    id from account_invoice
                    where origin in
                    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where journal_id=15))""")
                invoice_ids = cr.fetchall()
                invoice_id = [invoice[0] for invoice in invoice_ids]
                domain.append(('invoice','in',invoice_id))
                res['domain']['line_ids'] = domain
            elif bank.journal_id.code == 'appwx':
                #cr.execute("""select
                #    id from account_invoice
                #    where origin in
                #    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where ref ilike '4%'))""")
                cr.execute("""select
                    id from account_invoice
                    where origin in
                    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where journal_id=14))""")
                invoice_ids = cr.fetchall()
                invoice_id = [invoice[0] for invoice in invoice_ids]
                domain.append(('invoice','in',invoice_id))
                res['domain']['line_ids'] = domain
            elif bank.journal_id.code == 'alipa':
                #cr.execute("""select
                #    id from account_invoice
                #    where origin in
                #    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where ref ilike '4%'))""")
                cr.execute("""select
                    id from account_invoice
                    where origin in
                    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where journal_id=13))""")
                invoice_ids = cr.fetchall()
                invoice_id = [invoice[0] for invoice in invoice_ids]
                domain.append(('invoice','in',invoice_id))
                res['domain']['line_ids'] = domain
            elif bank.journal_id.code == 'BNK2':
                #cr.execute("""select
                #    id from account_invoice
                #    where origin in
                #    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where ref ilike '4%'))""")
                cr.execute("""select
                    id from account_invoice
                    where origin in
                    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where journal_id=11))""")
                invoice_ids = cr.fetchall()
                invoice_id = [invoice[0] for invoice in invoice_ids]
                domain.append(('invoice','in',invoice_id))
                res['domain']['line_ids'] = domain
            elif bank.journal_id.code == 'wxpay':
                #cr.execute("""select
                #    id from account_invoice
                #    where origin in
                #    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where ref ilike '4%'))""")
                cr.execute("""select
                    id from account_invoice
                    where origin in
                    (select name from ebiz_customer_complain where order_id in (select order_id from sale_payment_line where journal_id=12))""")
                invoice_ids = cr.fetchall()
                invoice_id = [invoice[0] for invoice in invoice_ids]
                domain.append(('invoice','in',invoice_id))
                res['domain']['line_ids'] = domain
            else:
                res['domain']['line_ids'] = domain
        return res
                

    def populate_statement(self, cr, uid, ids, context=None):
        context = dict(context or {})
        statement_id = context.get('statement_id', False)
        if not statement_id:
            return {'type': 'ir.actions.act_window_close'}
        data = self.read(cr, uid, ids, context=context)[0]
        line_ids = data['line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        currency_obj = self.pool.get('res.currency')
        line_date = time.strftime('%Y-%m-%d')
        statement = statement_obj.browse(cr, uid, statement_id, context=context)

        # for each selected move lines
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = line_date
            amount = 0.0

            if line.debit > 0:
                amount = line.debit
            elif line.credit > 0:
                amount = -line.credit

            if line.amount_currency:
                amount = currency_obj.compute(cr, uid, line.currency_id.id,
                    statement.currency.id, line.amount_currency, context=ctx)
            elif (line.invoice and line.invoice.currency_id.id != statement.currency.id):
                amount = currency_obj.compute(cr, uid, line.invoice.currency_id.id,
                    statement.currency.id, amount, context=ctx)

            context.update({'move_line_ids': [line.id],
                            'invoice_id': line.invoice.id})

            ref = ''
            if line.journal_id.code == 'SCNJ':
                complain_name = line.invoice.origin
                if complain_name:
                    complain_obj = self.pool['ebiz.customer.complain']
                    complain_id = complain_obj.search(cr, uid,[('name','=',complain_name)], context=context)
                    complain = complain_obj.browse(cr, uid, complain_id, context=context)
                    ref = complain.order_id.payment_lines.payorderosn or ''

            statement_line_obj.create(cr, uid, {
                'name': (line.journal_id.code == 'SCNJ') and line.invoice.payref or line.name or '?',
                'amount': amount,
                'partner_id': line.partner_id.id,
                'statement_id': statement_id,
                'ref': ref or line.ref,
                'date': statement.date,
            }, context=context)
        return {'type': 'ir.actions.act_window_close'}