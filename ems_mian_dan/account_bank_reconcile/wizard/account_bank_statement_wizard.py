# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import logging
import xlrd,time
from openerp.exceptions import ValidationError
try:
    import xlwt
except ImportError:
    xlwt = None
import base64
from cStringIO import StringIO

_logger = logging.getLogger(__name__)

class account_bank_statement_wizard(models.TransientModel):
    _name = 'account.bank.statement.wizard'
    _description = u'导入流水'

    bank_id = fields.Many2one('account.bank.statement', u'银行对账单')
    bank_statement_binary = fields.Binary(u'导入Excel')
    excel_lines = fields.One2many('account.bank.statement.wizard.line','wizard_id',u'流水号')

    @api.multi
    def button_confirm(self):
        sale_model = self.env['sale.order']
        invoice_model = self.env['account.invoice']
        error_row = 0
        try:
            for line in self.excel_lines:
                self.write({'excel_lines':[(2,line.id,0)]})
            excel = xlrd.open_workbook(file_contents=base64.decodestring(self.bank_statement_binary))
            sh = excel.sheet_by_index(0)
            line_vals = []
            for rx in range(1,sh.nrows):
                # date_point = time.localtime(sh.cell(rx,3).value)
                # date = time.strftime("%Y-%m-%d", date_point)
                error_row = rx
                journal_name = sh.cell(rx,0).value
                if unicode(journal_name) != self.bank_id.journal_id.name:continue
                date = sh.cell(rx,3).value
                date = isinstance(date,str) and date or isinstance(date,unicode) and date\
                or xlrd.xldate.xldate_as_datetime(date,0).strftime("%Y-%m-%d")
                ref = str(sh.cell(rx,2).value or '')
                name = str(sh.cell(rx,1).value or '')
                sale = sale_model.search([('payment_lines.payorderosn','ilike',ref+'%')])

                line_val = {
                        'date':date,
                        'ref':ref,
                        'name':name,
                        'amount':float(sh.cell(rx,4).value),
                        'partner_id':sale and sale[0].partner_invoice_id.id or False,
                        }

                # if self.bank_id.bank_statement_type == 'refund':
                #     line_val.update({'amount':float(sh.cell(rx,4).value) * -1})
                # if self.bank_id.bank_statement_type == 'receive':
                #     line_val.update({'amount':float(sh.cell(rx,4).value)})

                _logger.info(line_val)
                line_vals.append((0,0,line_val))
            self.write({'excel_lines':line_vals})
        except Exception, e:
            raise ValidationError("验证失败，错误行数：%s错误信息：%s"%(error_row,e))
        return {
            'name':u'导入流水',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_id':self.id,
            'res_model':'account.bank.statement.wizard',
            'target':'new',
        }

    @api.multi
    def button_import(self):
        invoice_model = self.env['account.invoice']
        line_vals = []
        for line in self.excel_lines:
            line_val = {
                'date':line.date,
                'ref':line.ref,
                'amount':line.amount,
                'name':line.name,
                'partner_id':line.partner_id.id,
            }
            line_vals.append((0,0,line_val))
        self.bank_id.write({'line_ids':line_vals})
        return True

class account_bank_statement_wizard_line(models.TransientModel):
    _name = 'account.bank.statement.wizard.line'
    _description = u'流水号'

    wizard_id = fields.Many2one('account.bank.statement.wizard',u'导入流水')
    date = fields.Date(u'日期')
    ref = fields.Char(u'参考')
    name = fields.Char(u'交流')
    partner_id = fields.Many2one('res.partner',u'客户')
    amount = fields.Float(u'总额')

