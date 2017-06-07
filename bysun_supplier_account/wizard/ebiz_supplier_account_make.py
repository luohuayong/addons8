# -*- coding: utf-8 -*- #
import time
from openerp.osv import osv, fields
from openerp import  exceptions
import logging
import openerp.addons.decimal_precision as dp
import datetime
from openerp.tools.translate import _
try:
    import xlwt
except ImportError:
    xlwt = None
import base64
from cStringIO import StringIO
logger = logging.getLogger(__name__)

class ebiz_supplier_account_join_statement(osv.osv_memory):
    _name = 'ebiz.supplier.account.join.statement'
    _description = u'加入对账单'

    _columns = {
        'statement_no':fields.char(u'对帐单编号'),
        }

    def join_statement(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]

        #检查对账单编号是否存在
        statement_no = False
        for statement_obj in self.browse(cr, uid, ids, context=context):
            statement_no = statement_obj.statement_no
        statement_ids = self.pool.get('ebiz.supplier.account.line').search(cr, uid, [('statement_no', '=', statement_no), ('state', '=', 'draft')], context=context)
        statement_id = statement_ids and statement_ids[0] or False
        if not statement_id:
            raise exceptions.ValidationError(u'未对账的对账单编号[%s]未找到，请重新输入！'%(statement_no))

        statement_obj = self.pool.get('ebiz.supplier.account.line').browse(cr ,uid, [statement_id], context=context)

        active_ids = context.get('active_ids',False)
        if (active_ids):
            lines = self.pool.get('ebiz.supplier.account.line').browse(cr, uid, active_ids, context=context)
        # 判断是否同一个公司，判断是否另外一张对账单的明细
            supplier = False
            for line in lines:
                if line.statement_no:
                    raise exceptions.ValidationError(u'不能把其它对账单的明细加入到另外一张对账单')
                if not supplier:
                    supplier = line.partner_id.id
                    continue
                if supplier != line.partner_id.id:
                    raise exceptions.ValidationError(u'不能把不同供应商的明细加入到同一张对账单里')
            if statement_obj and supplier != statement_obj.partner_id.id:
                raise exceptions.ValidationError(u'不能加入到另外一个供应商的对账单里')

            lines.write({'statement_no': statement_no})
        return {'type': 'ir.actions.act_window_close'}

class ebiz_supplier_account_export(osv.osv_memory):
    _name = 'ebiz.supplier.account.export'
    _description = u'导出结算明细'


    def _get_uom_translation(self, cr, uid, context=None):
        context = context or {}
        lang = False
        if context.get('lang', False):
            lang = context['lang']
        uom_ids = self.pool.get('product.uom').search(cr, uid, [], context=context)
        result = {}
        translation = self.pool.get('ir.translation')

        for obj in self.pool.get('product.uom').browse(cr, uid, uom_ids, context=context):
            if lang:
                trans_ids = translation.search(cr, uid, [('lang', '=', lang), ('src', '=', obj.name)], context=context)
                trans_id = trans_ids and trans_ids[0] or False
                if trans_id:
                    trans_obj = translation.browse(cr, uid, [trans_id], context=context)
                    if trans_obj:
                        result.update({obj.name: trans_obj.value})
                    else:
                        result.update({obj.name: obj.name})
                else:
                    result.update({obj.name: obj.name})
        return  result

    def from_data_not_commision(self, cr, uid, lines, supplier_mode_dict, state_dict, type_dict, unit_trans_dict, sequence, context=None):
        workbook = xlwt.Workbook()

        header_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
        content_title = xlwt.easyxf( "font: bold off; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )

        try:
            start_time = False
            end_time = False
            total_dict = {}
            supplier = False

            sheet1 = workbook.add_sheet(u'对账单')
            sheet2 = workbook.add_sheet(u'货款明细表')
            if (sheet2):
                index = 0
                startRow = 1

                sheet2.write(0, 0, u'产品')
                sheet2.write(0, 1, u'数量')
                sheet2.write(0, 2, u'单位')
                sheet2.write(0, 3, u'采购单价')
                sheet2.write(0, 4, u'采购金额')
                sheet2.write(0, 5, u'出库时间')
                sheet2.write(0, 6, u'状态')
                sheet2.write(0, 7, u'销售订单号')
                sheet2.write(0, 8, u'仓库调拨单号')

                for line in lines:
                    if supplier and supplier != line.partner_id.name:
                        raise exceptions.ValidationError(u'只能选择同一个供应商的结算明细！')
                    elif not supplier:
                        supplier = line.partner_id.name

                    if line.type in ['payment_goods', 'return_goods']:
                        if not total_dict.get(line.product_id.id, False):
                            total_dict.update({line.product_id.id: {line.standard_price: {
                                              'product_id': line.product_id.name,
                                              'standard_price': line.standard_price,
                                              'uom': unit_trans_dict[line.uom_id.name],
                                              'amount': line.amount,
                                              'purchase_total': line.purchase_total,
                                              'type': u'货款',
                                              'qty_send': line.qty_send,
                                              'state': state_dict[line.state],
                                              'sale_order_no': line.sale_id.name,
                                              'picking_no': line.picking_id.name,
                                              'qty_available': line.product_id.qty_available,
                                              }}})
                        elif not total_dict.get(line.product_id.id).get(line.standard_price, False):
                            total_dict.get(line.product_id.id).update({line.standard_price: {
                                              'product_id': line.product_id.name,
                                              'standard_price': line.standard_price,
                                              'uom': unit_trans_dict[line.uom_id.name],
                                              'amount': line.amount,
                                              'purchase_total': line.purchase_total,
                                              'type': u'货款',
                                              'qty_send': line.qty_send,
                                              'state': state_dict[line.state],
                                              'sale_order_no': line.sale_id.name,
                                              'picking_no': line.picking_id.name,
                                              'qty_available': line.product_id.qty_available,
                                              }})
                        else:
                            amount = total_dict.get(line.product_id.id).get(line.standard_price).get('amount', 0) + line.amount
                            purchase_total = total_dict.get(line.product_id.id).get(line.standard_price).get('purchase_total', 0) + line.purchase_total
                            total_dict.get(line.product_id.id).get(line.standard_price).update({
                                                      'product_id': line.product_id.name,
                                                      'standard_price': line.standard_price,
                                                      'uom': unit_trans_dict[line.uom_id.name],
                                                      'amount': amount,
                                                      'purchase_total': purchase_total,
                                                      'type': u'货款',
                                                      'qty_send': line.qty_send,
                                                      'state': state_dict[line.state],
                                                      'sale_order_no': line.sale_id.name,
                                                      'picking_no': line.picking_id.name,
                                                      'qty_available': line.product_id.qty_available,
                                                      }
                                                  )

                        if not start_time or float(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))) > float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            start_time = line.qty_send
                        if not end_time or float(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))) < float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            end_time = line.qty_send

                        if line.product_id.name:
                            sheet2.write(startRow + index, 0, line.product_id.name, content_title)
                        if line.amount:
                            sheet2.write(startRow + index, 1, line.amount, content_title)
                        if line.uom_id:
                            sheet2.write(startRow + index, 2, unit_trans_dict[line.uom_id.name], content_title)
                        if line.standard_price:
                            sheet2.write(startRow + index, 3, line.standard_price, content_title)
                        if line.purchase_total:
                            sheet2.write(startRow + index, 4, line.purchase_total, content_title)
                        if line.qty_send:
                            sheet2.write(startRow + index, 5, line.qty_send, content_title)
                        if line.state:
                            sheet2.write(startRow + index, 6, state_dict[line.state], content_title)
                        if line.sale_id:
                            sheet2.write(startRow + index, 7, line.sale_id.name, content_title)
                        if line.picking_id:
                            sheet2.write(startRow + index, 8, line.picking_id.name, content_title)
                        index += 1

            if (sheet1):
                sheet1.write_merge(0, 0, 0, 6, u'对账单')
                sheet1.write(1, 0, u'对账单编号:')
                sheet1.write(1, 1, sequence)
                sheet1.write(2, 0, u'供应商名称:')
                sheet1.write(2, 1, supplier)
                sheet1.write(3, 0, u'本次对账起止时间:')
                sheet1.write(4, 0, u'本期货款明细:')
                sheet1.write(5, 0, u'序号')
                sheet1.write(5, 1, u'产品')
                sheet1.write(5, 2, u'数量')
                sheet1.write(5, 3, u'单位')
                sheet1.write(5, 4, u'采购单价')
                sheet1.write(5, 5, u'采购金额')
                sheet1.write(5, 6, u'库存')
                startRow = 6
                index = 1
                purchase_total = 0
                cost_total = 0
                for key1 in total_dict.keys():
                    for key2 in total_dict.get(key1).keys():
                        sheet1.write(startRow, 0, index)
                        sheet1.write(startRow, 1, total_dict.get(key1).get(key2).get('product_id'))
                        sheet1.write(startRow, 2, total_dict.get(key1).get(key2).get('amount'))
                        sheet1.write(startRow, 3, total_dict.get(key1).get(key2).get('uom'))
                        sheet1.write(startRow, 4, total_dict.get(key1).get(key2).get('standard_price'))
                        sheet1.write(startRow, 5, total_dict.get(key1).get(key2).get('purchase_total'))
                        sheet1.write(startRow, 6, total_dict.get(key1).get(key2).get('qty_available'))
                        purchase_total += total_dict.get(key1).get(key2).get('purchase_total')
                        startRow += 1
                        index += 1

                startRow += 2
                sheet1.write(startRow, 0, u'本期费用明细:')
                startRow += 1

                sheet1.write(startRow, 0, u'序号')
                sheet1.write(startRow, 1, u'项目')
                sheet1.write(startRow, 2, u'金额')
                sheet1.write(startRow, 3, u'销售订单编号')
                sheet1.write(startRow, 4, u'备注')
                startRow += 1
                index = 1

                for line in lines:
                    if line.type == 'cost':
                        if not start_time or float(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))) > float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            start_time = line.qty_send
                        if not end_time or float(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))) < float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            end_time = line.qty_send

                        sheet1.write(startRow, 0, index)
                        sheet1.write(startRow, 1, line.product_id.name)
                        sheet1.write(startRow, 2, line.purchase_total)
                        sheet1.write(startRow, 3, line.sale_id.name or '')
                        sheet1.write(startRow, 4, line.notes)
                        cost_total += line.purchase_total
                        startRow += 1
                        index += 1

                sheet1.write(3, 1, start_time + u'～' + end_time)

                startRow += 2
                sheet1.write(startRow, 0, u'本期货款合计:')
                sheet1.write(startRow, 1, purchase_total)
                sheet1.write(startRow + 1, 0, u'本期费用合计:')
                sheet1.write(startRow + 1, 1, cost_total)
                sheet1.write(startRow + 2, 0, u'应付金额合计:')
                sheet1.write(startRow + 2, 1, purchase_total + cost_total)

                sheet1.write(startRow + 4, 0, u'备注:')
                sheet1.write(startRow + 4, 1, u'请对账无误后按照货款金额开具等额发票寄至公司结算。')
                sheet1.write(startRow + 5, 1, u'库存数量为导出对账单时间的实时库存。')

        except Exception, ex:
            print Exception, ":", ex

        fp = StringIO()
        workbook.save( fp )
        fp.seek( 0 )
        data = fp.read()
        fp.close()
        return data

    def from_data_commision(self, cr, uid, lines, supplier_mode_dict, state_dict, type_dict, unit_trans_dict, sequence, context=None):
        workbook = xlwt.Workbook()

        header_title = xlwt.easyxf( "font: bold on; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )
        content_title = xlwt.easyxf( "font: bold off; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center" )

        try:
            total_dict = {}
            supplier = False
            start_time = False
            end_time = False

            sheet1 = workbook.add_sheet(u'对账单')
            sheet2 = workbook.add_sheet(u'货款明细表')
            if (sheet2):
                index = 0
                startRow = 1

                sheet2.write(0, 0, u'产品')
                sheet2.write(0, 1, u'数量')
                sheet2.write(0, 2, u'单位')
                sheet2.write(0, 3, u'销售单价')
                sheet2.write(0, 4, u'销售金额')
                sheet2.write(0, 5, u'采购单价')
                sheet2.write(0, 6, u'采购金额')
                sheet2.write(0, 7, u'佣金')
                sheet2.write(0, 8, u'出库时间')
                sheet2.write(0, 9, u'状态')
                sheet2.write(0, 10, u'销售订单号')
                sheet2.write(0, 11, u'仓库调拨单号')

                for line in lines:
                    if supplier and supplier != line.partner_id.name:
                        raise exceptions.ValidationError(u'只能选择同一个供应商的结算明细！')
                    elif not supplier:
                        supplier = line.partner_id.name

                    if line.type in ['payment_goods', 'return_goods']:
                        if not total_dict.get(line.product_id.id, False):
                            standard_price_section = {line.standard_price: {
                                                      'product_id': line.product_id.name,
                                                      'unit_price': line.unit_price,
                                                      'standard_price': line.standard_price,
                                                      'uom': unit_trans_dict[line.uom_id.name],
                                                      'amount': line.amount,
                                                      'subtotal': line.subtotal,
                                                      'purchase_total': line.purchase_total,
                                                      'commission': line.commission,
                                                      'type': '货款',
                                                      'qty_send': line.qty_send,
                                                      'state': state_dict[line.state],
                                                      'sale_order_no': line.sale_id.name,
                                                      'picking_no': line.picking_id.name,
                                                      'qty_available': line.product_id.qty_available,
                                                      }
                                                  }
                            unit_price_section = {line.unit_price: standard_price_section}
                            product_section = {line.product_id.id: unit_price_section}
                            total_dict.update(product_section)
                        elif not total_dict.get(line.product_id.id).get(line.unit_price, False):
                            standard_price_section = {line.standard_price: {
                                                      'product_id': line.product_id.name,
                                                      'unit_price': line.unit_price,
                                                      'standard_price': line.standard_price,
                                                      'uom': unit_trans_dict[line.uom_id.name],
                                                      'amount': line.amount,
                                                      'subtotal': line.subtotal,
                                                      'purchase_total': line.purchase_total,
                                                      'commission': line.commission,
                                                      'type': '货款',
                                                      'qty_send': line.qty_send,
                                                      'state': state_dict[line.state],
                                                      'sale_order_no': line.sale_id.name,
                                                      'picking_no': line.picking_id.name,
                                                      'qty_available': line.product_id.qty_available,
                                                      }
                                                  }
                            unit_price_section = {line.unit_price: standard_price_section}
                            total_dict.get(line.product_id.id).update(unit_price_section)
                        elif not total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price, False):
                            standard_price_section = {line.standard_price: {
                                                      'product_id': line.product_id.name,
                                                      'unit_price': line.unit_price,
                                                      'standard_price': line.standard_price,
                                                      'uom': unit_trans_dict[line.uom_id.name],
                                                      'amount': line.amount,
                                                      'subtotal': line.subtotal,
                                                      'purchase_total': line.purchase_total,
                                                      'commission': line.commission,
                                                      'type': '货款',
                                                      'qty_send': line.qty_send,
                                                      'state': state_dict[line.state],
                                                      'sale_order_no': line.sale_id.name,
                                                      'picking_no': line.picking_id.name,
                                                      'qty_available': line.product_id.qty_available,
                                                      }
                                                  }
                            total_dict.get(line.product_id.id).get(line.unit_price).update(standard_price_section)
                        else:
                            amount = total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price).get('amount', 0) + line.amount
                            subtotal = total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price).get('subtotal', 0) + line.subtotal
                            purchase_total = total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price).get('purchase_total', 0) + line.purchase_total
                            commission = total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price).get('commission', 0) + line.commission
                            total_dict.get(line.product_id.id).get(line.unit_price).get(line.standard_price).update({
                                                      'product_id': line.product_id.name,
                                                      'unit_price': line.unit_price,
                                                      'standard_price': line.standard_price,
                                                      'uom': unit_trans_dict[line.uom_id.name],
                                                      'amount': amount,
                                                      'subtotal': subtotal,
                                                      'purchase_total': purchase_total,
                                                      'commission': commission,
                                                      'type': '货款',
                                                      'qty_send': line.qty_send,
                                                      'state': state_dict[line.state],
                                                      'sale_order_no': line.sale_id.name,
                                                      'picking_no': line.picking_id.name,
                                                      'qty_available': line.product_id.qty_available,
                                                      })

                        if not start_time or float(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))) > float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            start_time = line.qty_send
                        if not end_time or float(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))) < float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            end_time = line.qty_send

                        if line.product_id.name:
                            sheet2.write(startRow + index, 0, line.product_id.name, content_title)
                        if line.amount:
                            sheet2.write(startRow + index, 1, line.amount, content_title)
                        if line.uom_id:
                            sheet2.write(startRow + index, 2, unit_trans_dict[line.uom_id.name], content_title)
                        if line.unit_price:
                            sheet2.write(startRow + index, 3, line.unit_price, content_title)
                        if line.subtotal:
                            sheet2.write(startRow + index, 4, line.subtotal, content_title)
                        if line.standard_price:
                            sheet2.write(startRow + index, 5, line.standard_price, content_title)
                        if line.purchase_total:
                            sheet2.write(startRow + index, 6, line.purchase_total, content_title)
                        if line.commission:
                            sheet2.write(startRow + index, 7, line.commission, content_title)
                        if line.qty_send:
                            sheet2.write(startRow + index, 8, line.qty_send, content_title)
                        if line.state:
                            sheet2.write(startRow + index, 9, state_dict[line.state], content_title)
                        if line.sale_id:
                            sheet2.write(startRow + index, 10, line.sale_id.name, content_title)
                        if line.picking_id:
                            sheet2.write(startRow + index, 11, line.picking_id.name, content_title)
                        index += 1

            if (sheet1):
                index = 0
                startRow = 6

                sheet1.write_merge(0, 0, 0, 9, u'对账单')
                sheet1.write(1, 0, u'对账单编号:')
                sheet1.write(1, 1, sequence)
                sheet1.write(2, 0, u'供应商名称:')
                sheet1.write(2, 1, supplier)
                sheet1.write(3, 0, u'本次对账起止时间:')
                sheet1.write(4, 0, u'本期货款明细:')
                sheet1.write(5, 0, u'序号')
                sheet1.write(5, 1, u'产品')
                sheet1.write(5, 2, u'数量')
                sheet1.write(5, 3, u'单位')
                sheet1.write(5, 4, u'销售单价')
                sheet1.write(5, 5, u'销售金额')
                sheet1.write(5, 6, u'采购单价')
                sheet1.write(5, 7, u'采购金额')
                sheet1.write(5, 8, u'佣金')
                sheet1.write(5, 9, u'库存')

                subtotal = 0
                purchase_total = 0
                cost_total = 0
                index = 1

                for key1 in total_dict.keys():
                    for key2 in total_dict.get(key1).keys():
                        for key3 in total_dict.get(key1).get(key2).keys():
                            sheet1.write(startRow, 0, index)
                            sheet1.write(startRow, 1, total_dict.get(key1).get(key2).get(key3).get('product_id'))
                            sheet1.write(startRow, 2, total_dict.get(key1).get(key2).get(key3).get('amount'))
                            sheet1.write(startRow, 3, total_dict.get(key1).get(key2).get(key3).get('uom'))
                            sheet1.write(startRow, 4, total_dict.get(key1).get(key2).get(key3).get('unit_price'))
                            sheet1.write(startRow, 5, total_dict.get(key1).get(key2).get(key3).get('subtotal'))
                            sheet1.write(startRow, 6, total_dict.get(key1).get(key2).get(key3).get('standard_price'))
                            sheet1.write(startRow, 7, total_dict.get(key1).get(key2).get(key3).get('purchase_total'))
                            sheet1.write(startRow, 8, total_dict.get(key1).get(key2).get(key3).get('commission'))
                            sheet1.write(startRow, 9, total_dict.get(key1).get(key2).get('qty_available'))

                            subtotal += total_dict.get(key1).get(key2).get(key3).get('subtotal')
                            purchase_total += total_dict.get(key1).get(key2).get(key3).get('purchase_total')
                            startRow += 1
                            index += 1

                sheet1.write(startRow, 0, u'本期费用明细:')
                startRow += 1

                sheet1.write(startRow, 0, u'序号')
                sheet1.write(startRow, 1, u'项目')
                sheet1.write(startRow, 2, u'金额')
                sheet1.write(startRow, 3, u'销售订单编号')
                sheet1.write(startRow, 4, u'备注')
                startRow += 1
                index = 1

                for line in lines:
                    if line.type == 'cost':
                        if not start_time or float(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))) > float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            start_time = line.qty_send
                        if not end_time or float(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))) < float(time.mktime(time.strptime(line.qty_send, '%Y-%m-%d %H:%M:%S'))):
                            end_time = line.qty_send

                        sheet1.write(startRow, 0, index)
                        sheet1.write(startRow, 1, line.product_id.name)
                        sheet1.write(startRow, 2, line.purchase_total)
                        sheet1.write(startRow, 3, line.sale_id.name or '')
                        sheet1.write(startRow, 4, line.notes)
                        cost_total += line.purchase_total
                        startRow += 1
                        index += 1

                sheet1.write(3, 1, start_time + u'～' + end_time)

                sheet1.write(startRow, 0, u'本期销售收入合计:')
                sheet1.write(startRow, 1, subtotal)
                sheet1.write(startRow + 1, 0, u'本期代理费用合计:')
                sheet1.write(startRow + 1, 1, subtotal - purchase_total)
                sheet1.write(startRow + 2, 0, u'本期其他费用合计:')
                sheet1.write(startRow + 2, 1, cost_total)
                sheet1.write(startRow + 3, 0, u'应付金额合计:')
                sheet1.write(startRow + 3, 1, purchase_total + cost_total)

                sheet1.write(startRow + 4, 0, u'备注:')
                sheet1.write(startRow + 4, 1, u'库存数量为导出对账单时间的实时库存。')

        except Exception, ex:
            print Exception, ":", ex

        fp = StringIO()
        workbook.save( fp )
        fp.seek( 0 )
        data = fp.read()
        fp.close()
        return data

    def from_data(self, cr, uid, lines, sequence, context=None):
        supplier_mode_dict = {'Direct_Procurement': u'直采',
                                'Consign_stock_in': u'代售入仓',
                                'Consign': u'代售不入仓',
                                'Commission':u'佣金'}
        state_dict = {'draft':u'未对账','checked':u'已对账','settled':u'已结算','cancelled':u'已取消'}
        type_dict = {'payment_goods':u'货款','commission':u'佣金','cost':u'费用','return_goods':u'退货'}

        unit_trans_dict = self._get_uom_translation(cr, uid, context=context)

        line = lines and lines[0] or False
        if line:
            if line.supplier_mode in ['Consign_stock_in','Consign']:
                return self.from_data_not_commision(cr, uid, lines, supplier_mode_dict, state_dict, type_dict, unit_trans_dict, sequence, context=context)
            elif line.supplier_mode == 'Commission':
                return self.from_data_commision(cr, uid, lines, supplier_mode_dict, state_dict, type_dict, unit_trans_dict, sequence, context=context)
            else:
                raise exceptions.ValidationError(u'请选择正确的供应商！')
        else:
            raise exceptions.ValidationError(u'列表中没有数据！')


    def action_export_lines(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids',False)
        if (active_ids):
            lines = self.pool.get('ebiz.supplier.account.line').browse(cr, uid, active_ids, context=context)
            statement_no = 'statement_no'
            sequence = False
            supplier = False
            for line in lines:
                if statement_no == 'statement_no':
                    statement_no = line.statement_no
                    supplier = line.partner_id.name
                    continue
                if statement_no != line.statement_no:
                    raise exceptions.ValidationError(u'选择的列表中只能存在一个对账单编号！')

                if supplier and supplier != line.partner_id.name:
                    raise exceptions.ValidationError(u'只能选择同一个供应商的结算明细！')

            if not statement_no:
                sequence = self.pool.get('ir.sequence').get(cr, uid, 'ebiz.supplier.account', context=context) or '/'
            else:
                sequence = statement_no
            data = base64.encodestring(self.from_data(cr, uid, lines, sequence, context=context))

            attach_vals = {
                     'name':u'对账单_' + sequence + '.xls',
                     'datas':data,
                     'datas_fname':'sale_order.xls',
                     }
            try:
                attach_obj = self.pool.get('ir.attachment')
                doc_id = attach_obj.create(cr, uid, attach_vals)
            except Exception,ex:
                print Exception,":",ex
            if not statement_no:
                lines.write({'statement_no': sequence})

            return {
                'type' : 'ir.actions.act_url',
                'url':   '/web/binary/saveas?model=ir.attachment&field=datas&filename_field=name&id=%s' % ( doc_id ),
                'target': 'self',
                }

ebiz_supplier_account_export()

class ebiz_supplier_account_invoice(osv.osv_memory):
    _name = 'ebiz.supplier.account.invoice'
    _description = "Ebiz Supplier Account Invoice"

    def create_invoice_action(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids',False)
        if (active_ids):
            for obj in self.pool.get('ebiz.supplier.account.line').browse(cr, uid, active_ids, context=context):
                if obj.state != 'checked':
                    raise osv.except_osv(_(u'警告!'), _(u'只能选择状态为‘已对账’的明细行！'))
            invoice_id = self.pool.get('ebiz.supplier.account.line').create_account_invoice(cr, uid, active_ids, context=context)

            return {
                    'res_id': invoice_id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
            }
ebiz_supplier_account_invoice()

class ebiz_supplier_account_checked(osv.osv_memory):
    _name = 'ebiz.supplier.account.checked'
    _description = "Settled Ebiz Supplier Account"

    def save_action(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids',False)
        for obj in self.pool.get('ebiz.supplier.account.line').browse(cr, uid, active_ids, context=context):
            if obj.state != 'draft' or not obj.statement_no:
                raise osv.except_osv(_(u'警告!'), _(u'只能选择状态为‘未对账’的并且有对账单编号的明细行！'))
            obj.write({'state':'checked'})
        return {'type': 'ir.actions.act_window_close'}

ebiz_supplier_account_checked()

class ebiz_supplier_account_cancelled(osv.osv_memory):
    _name = 'ebiz.supplier.account.cancelled'
    _description = "Cancelled Ebiz Supplier Account"

    def save_action(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids',False)
        for obj in self.pool.get('ebiz.supplier.account.line').browse(cr, uid, active_ids, context=context):
            if obj.state == 'settled':
                raise osv.except_osv(_(u'警告!'), _(u'不能选择状态为‘已结算’的单据！'))
            obj.write({'state':'cancelled'})
            self.pool.get('stock.move').write(cr, uid, obj.move_id.id, {'is_import_supplier_account':False})
        return {'type': 'ir.actions.act_window_close'}
        
ebiz_supplier_account_cancelled()