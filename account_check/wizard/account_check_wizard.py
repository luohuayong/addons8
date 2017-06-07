# -*- coding: utf-8 -*-

from openerp import api, fields, models, _

class account_check_wizard(models.TransientModel):
    _name = 'account.check.wizard'
    _description = u'商品、供应商会计检查'

    error_items = fields.One2many('account.check.wizard.line', 'wizard_id', u'错误明细')

    @api.model
    def default_get(self, fields):
        product_model = self.env['product.product']
        supplier_model = self.env['res.partner']
        res = super(account_check_wizard, self).default_get(fields)
        error_list = []
        # price_error_id = product_model.search(['|',('purchase_price','=',0),('standard_price','=',0),\
        #     ('active','=',True),('type','!=','service')])
        # if price_error_id:
        #     error_list += [(0,0,{'error_item':price_error.display_name,'error_info':u'商品价格错误'}) for price_error in price_error_id]
        # tax_empty_id = product_model.search(['|','|','|',('property_account_expense','=',False),('property_account_income','=',False),('taxes_id','=',False),('supplier_taxes_id','=',False),\
        #    ('active','=',True),('type','!=','service')])
        tax_empty_id = product_model.search(['|',('taxes_id','=',False),('supplier_taxes_id','=',False),\
            ('active','=',True),('type','!=','service')])
        if tax_empty_id:
            error_list += [(0,0,{'error_item':tax_empty.display_name,'error_info':u'库存商品的税率未设置'}) for tax_empty in tax_empty_id]
        tax_error_id5 = product_model.search([('taxes_id','!=',False),('taxes_id.amount','<>',0.00),\
            ('seller_id.supplier_mode','=','Commission'),('active','!=',False),('type','!=','service')])
        if tax_error_id5:
            error_list += [(0,0,{'error_item':tax_error5.display_name,'error_info':u'佣金类商品税率设置不正确'}) for tax_error5 in tax_error_id5]
        tax_error_id = product_model.search([('supplier_taxes_id','!=',False),('supplier_taxes_id.amount','<>',0.00),\
            ('seller_id.supplier_mode','=','Commission'),('active','!=',False),('type','!=','service')])
        if tax_error_id:
            error_list += [(0,0,{'error_item':tax_error.display_name,'error_info':u'佣金类商品税率设置不正确'}) for tax_error in tax_error_id]    
        tax_error_id2 = product_model.search(['|',('supplier_taxes_id.amount','not in',(0.17,0.13)),('taxes_id.amount','<>',0.17),('seller_id.taxtype','=','general'),\
            ('active','=',True),('seller_id.supplier_mode','!=','Commission'),('type','!=','service')])
        if tax_error_id2:
            error_list += [(0,0,{'error_item':tax_error2.display_name,'error_info':u'一般纳税人非佣金型供应商相关产品税率不正确'}) for tax_error2 in tax_error_id2]
        tax_error_id3 = product_model.search(['|',('supplier_taxes_id.amount','<>',0.03),('taxes_id.amount','<>',0.17),('seller_id.taxtype','=','littlescope'),\
            ('active','=',True),('seller_id.supplier_mode','!=','Commission'),('type','!=','service')])
        if tax_error_id3:
            error_list += [(0,0,{'error_item':tax_error3.display_name,'error_info':u'小规模纳税人非佣金型供应商相关产品税率不正确'}) for tax_error3 in tax_error_id3]
        supplier_error_id = product_model.search([('active','=',True),('seller_id','=',False),('type','!=','service')])
        if supplier_error_id:
            error_list += [(0,0,{'error_item':supplier_error.display_name,'error_info':u'商品的供应商未设置'}) for supplier_error in supplier_error_id]
        account_error_id = product_model.search(['|','|',('categ_id','=',False),('categ_id.property_account_income_categ.code','!=','1016'),('categ_id.property_account_expense_categ.code','!=','1016'),\
            ('seller_id.supplier_mode','=','Commission'),('active','=',True)])
        if account_error_id:
            error_list += [(0,0,{'error_item':account_error.display_name,'error_info':u'佣金类商品"<内部分类>"的收入、费用科目应为[1016]代收款'}) for account_error in account_error_id]
        account_error_id1 = product_model.search(['|','|','|',('property_account_income','=',False),('property_account_expense','=',False),('property_account_income.code','!=','6001'),('property_account_expense.code','!=','6401'),\
            ('seller_id.supplier_mode','!=','Commission'),('active','=',True),('type','!=','service')])
        if account_error_id1:
            error_list += [(0,0,{'error_item':account_error1.display_name,'error_info':u'非佣金类商品收入应为[6001]主营业务收入、费用科目应为[6401]主营业务成本'}) for account_error1 in account_error_id1]
        account_payable_error_id = supplier_model.search([('property_account_payable.code','!=','2241'),('supplier','=',True),\
            ('supplier_mode','=','Commission'),('active','=',True)])
        if account_payable_error_id:
            error_list += [(0,0,{'error_item':account_payable_error.name,'error_info':u'佣金类供应商应付科目不为"[2241]其他应付款"'}) for account_payable_error in account_payable_error_id]
        account_payable_error_id2 = supplier_model.search([('property_account_payable.code','!=','2202'),('supplier','=',True),\
            ('supplier_mode','!=','Commission'),('active','=',True)])
        if account_payable_error_id2:
            error_list += [(0,0,{'error_item':account_payable_error2.name,'error_info':u'非佣金类供应商应付科目不为"[2202]应付账款"'}) for account_payable_error2 in account_payable_error_id2]
        res.update({'error_items':error_list})
        return res

class account_check_wizard_line(models.TransientModel):
    _name = 'account.check.wizard.line'
    _description = u'商品、供应商会计检查明细'

    error_item = fields.Char(u'商品SKU/供应商')
    error_info = fields.Char(u'错误提示')
    wizard_id = fields.Many2one('account.check.wizard', u'商品、供应商会计检查')

