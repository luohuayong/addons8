# -*- coding: utf-8 -*- #
from openerp import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_total = sum(line.price_unit * line.quantity for line in self.invoice_line)
        self.amount_tax = self.amount_total - self.amount_untaxed

class account_invoice_tax(models.Model):
    _inherit = "account.invoice.tax"
    
    @api.v8
    def compute(self, invoice):
        """修正税额之和，使其等于 总金额 减去 未税额
        """
        tax_grouped = super(account_invoice_tax, self).compute(invoice)
        tax_invoice = invoice.amount_total - invoice.amount_untaxed
        tax_total = sum(t['amount'] for t in tax_grouped.values())
        tax_diff = tax_total - tax_invoice 
        for t in tax_grouped.values():
            if t['amount'] > abs(tax_diff): 
                t['amount'] = t['amount'] - tax_diff
                break

        return tax_grouped
