# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _
import logging
import datetime
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    @api.multi
    def auto_reconcile_bank_statement(self):
        
        for bank_statement in self:
            for bank_line in bank_statement.line_ids:
                bank_line.auto_reconcile_bank_statement()
                obj_so = self.env['sale.payment.line'].search([('ref', 'ilike', bank_line.name.strip()),('payorderosn', 'ilike', bank_line.ref.strip())])
                datalist=u'SO号,金额\n'
                for list in obj_so:
                    datalist = datalist + str(list.order_id.name) + ',' + str(list.amount) + '\n'
                bank_line.write( {'note': datalist})
        return True
account_bank_statement()#对象定义结束

class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'
account_bank_statement_line()#对象定义结束