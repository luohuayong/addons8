# -*- coding: utf-8 -*- #
from openerp import tools
from openerp.osv import osv, fields
import logging
import time

_logger = logging.getLogger(__name__)
class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'account_move_id': fields.many2one('account.move', u'入库核算会计凭证', copy=False),
        'account_move_id_out': fields.many2one('account.move', u'出库核算会计凭证', copy=False),
    }

    def create_receipt_entry(self, cr, uid, ids, period_id, journal_id, account_id = None, context=None):
        move_obj = self.pool.get('account.move')
        product_obj = self.pool.get('product.template')
        entry_ids = []

        for picking in self.browse(cr, uid, ids, context=context):

            if (picking.state != 'done') or picking.account_move_id or \
                (not picking.move_lines) or (not picking.picking_type_id.is_create_entry):
                continue

            account_lines = []
            total_amount = 0.0
            for move in picking.move_lines:
                if move.product_id.is_combination:
                    production_model = self.pool['stock.production']
                    for quant in move.quant_ids:
                        production_ids = production_model.search(cr, uid, [('stock_lot','=',quant.lot_id and quant.lot_id.id or False), \
                            ('product_id','=',move.product_id.id),('state','=','confirm')])
                        if not production_ids:
                            raise osv.except_osv((u'错误!'), \
                                (u'未找到组合产品对应的加工单:产品名称-%s;批次号-%s'%(move.product_id.display_name,quant.lot_id.name))) 
                        productions = production_model.browse(cr, uid, production_ids[0])
                        raw_picking_ids = self.search(cr, uid, [('origin','=',productions.name), \
                            ('state','=','done'),('picking_type_code','=','outgoing')])
                        if not raw_picking_ids:
                            raise osv.except_osv((u'错误!'), \
                             (u'未找到组合产品对应的加工领料单或者领料单没有出库:产品名称-%s;批次号-%s'%(move.product_id.display_name,quant.lot_id.name))) 
                        raw_pickings = self.browse(cr, uid, raw_picking_ids[0])
                        for raw_move in raw_pickings.move_lines:
                            supplier_modes = raw_move.product_id.seller_ids.name.supplier_mode
                            if move.picking_type_id.code != 'incoming' and (supplier_modes != 'Consign_stock_in'):
                                continue
                            elif move.picking_type_id.code == 'incoming' and (supplier_modes == 'Consign_stock_in'):
                                continue
                            accounts = product_obj.get_product_accounts(cr, uid, raw_move.product_id.product_tmpl_id.id, context)
                            quantity = (raw_move.product_uom_qty / productions.product_uom_qty) * move.product_uom_qty
                            account_ids = account_id or ((supplier_modes in ('Consign_stock_in','Direct_Procurement')) and \
                                move.product_id.categ_id.property_stock_account_input_categ.id \
                                or move.product_id.categ_id.property_account_expense_categ.id)

                            debit_line_vals = {
                                'name': raw_move.name,
                                'product_id': raw_move.product_id.id,
                                'quantity': quantity,
                                'product_uom_id': raw_move.product_uom.id,
                                'ref': picking.name or False,
                                'date': move.date,
                                'partner_id': picking.partner_id and picking.partner_id.id,
                                'credit':  0,
                                'debit':  raw_move.price_unit * quantity,
                                'account_id': accounts['property_stock_valuation_account_id'],
                            }

                            credit_line_vals = {  
                                'name': raw_move.name,
                                'product_id': raw_move.product_id.id,
                                'quantity': quantity,
                                'product_uom_id': raw_move.product_uom.id,
                                'ref': picking.name or False,
                                'date': move.date,
                                'partner_id': picking.partner_id and picking.partner_id.id,
                                'credit': raw_move.price_unit * quantity,
                                'debit':  0,
                                'account_id': account_ids,
                            }

                            account_lines.append( (0, 0, credit_line_vals) )
                            account_lines.append( (0, 0, debit_line_vals) )
                else:
                    accounts = product_obj.get_product_accounts(cr, uid, move.product_id.product_tmpl_id.id, context)
                    valuation_amount = move.price_unit * move.product_uom_qty
                    supplier_modes = move.product_id.seller_ids.name.supplier_mode
                    if move.picking_type_id.code != 'incoming' and (supplier_modes != 'Consign_stock_in'):
                        continue
                    elif move.picking_type_id.code == 'incoming' and (supplier_modes == 'Consign_stock_in'):
                        continue
                    account_ids = account_id or ((supplier_modes in ('Consign_stock_in','Direct_Procurement')) and \
                                move.product_id.categ_id.property_stock_account_input_categ.id \
                                or move.product_id.categ_id.property_account_expense_categ.id)
                    debit_line_vals = {
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_uom_qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': picking.name or False,
                        'date': move.date,
                        'partner_id': picking.partner_id and picking.partner_id.id,
                        'credit':  0,
                        'debit':  valuation_amount,
                        'account_id': accounts['property_stock_valuation_account_id'],
                    }

                    credit_line_vals = {  
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_uom_qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': picking.name or False,
                        'date': move.date,
                        'partner_id': picking.partner_id and picking.partner_id.id,
                        'credit': valuation_amount ,
                        'debit':  0,
                        'account_id': account_ids,
                    }

                    account_lines.append( (0, 0, credit_line_vals) )
                    account_lines.append( (0, 0, debit_line_vals) )

            if not account_lines:continue

            account_move_id = move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': account_lines,
                                      'period_id': period_id,
                                      'date': picking.date_done,
                                      'ref': "%s:%s" % (picking.origin or '',  picking.name or '') }, context=context)
            self.write(cr, uid, picking.id, {'account_move_id': account_move_id })
            entry_ids.append(account_move_id)
        return entry_ids

    def create_delivery_entry(self, cr, uid, ids, period_id, journal_id, account_id = None, context=None):
        """创建出库成本结转会计凭证
        """
        move_obj = self.pool.get('account.move')
        product_obj = self.pool.get('product.template')
        entry_ids = []
        for picking in self.browse(cr, uid, ids, context=context):
            if (picking.state != 'done') or picking.account_move_id_out or \
                (picking.picking_type_id.code != 'outgoing') or \
                (not picking.move_lines) or (not picking.picking_type_id.is_create_entry):
                continue

            account_lines = []
            for move in picking.move_lines:
                if move.product_id.is_combination:
                    production_model = self.pool['stock.production']
                    for quant in move.quant_ids:
                        production_ids = production_model.search(cr, uid, [('stock_lot','=',quant.lot_id and quant.lot_id.id or False), \
                            ('product_id','=',move.product_id.id),('state','=','confirm')])
                        if not production_ids:
                            raise osv.except_osv((u'错误!'), \
                                (u'未找到组合产品对应的加工单:产品名称-%s;批次号-%s'%(move.product_id.display_name,quant.lot_id.name))) 
                        productions = production_model.browse(cr, uid, production_ids[0])
                        raw_picking_ids = self.search(cr, uid, [('origin','=',productions.name), \
                            ('state','=','done'),('picking_type_code','=','outgoing')])
                        if not raw_picking_ids:
                            raise osv.except_osv((u'错误!'), \
                             (u'未找到组合产品对应的加工领料单或者领料单没有出库:产品名称-%s;批次号-%s'%(move.product_id.display_name,quant.lot_id.name))) 
                        raw_pickings = self.browse(cr, uid, raw_picking_ids[0])
                        for raw_move in raw_pickings.move_lines:
                            supplier_modes = raw_move.product_id.seller_ids.name.supplier_mode
                            accounts = product_obj.get_product_accounts(cr, uid, raw_move.product_id.product_tmpl_id.id, context)
                            quantity = (raw_move.product_uom_qty / productions.product_uom_qty) * move.product_uom_qty
                            account_ids = account_id or ((supplier_modes in ('Consign_stock_in','Direct_Procurement')) and \
                                move.product_id.property_account_expense.id \
                                or move.product_id.categ_id.property_account_expense_categ.id)

                            debit_line_vals = {
                                'name': raw_move.name,
                                'product_id': raw_move.product_id.id,
                                'quantity': quantity,
                                'product_uom_id': raw_move.product_uom.id,
                                'ref': picking.name or False,
                                'date': move.date,
                                'partner_id': picking.partner_id and picking.partner_id.id,
                                'credit':  0,
                                'debit':  raw_move.price_unit * quantity,
                                'account_id': account_ids,
                            }

                            credit_line_vals = {  
                                'name': raw_move.name,
                                'product_id': raw_move.product_id.id,
                                'quantity': quantity,
                                'product_uom_id': raw_move.product_uom.id,
                                'ref': picking.name or False,
                                'date': move.date,
                                'partner_id': picking.partner_id and picking.partner_id.id,
                                'credit': raw_move.price_unit * quantity,
                                'debit':  0,
                                'account_id': accounts['property_stock_valuation_account_id'],
                            }

                            account_lines.append( (0, 0, credit_line_vals) )
                            account_lines.append( (0, 0, debit_line_vals) ) 
                else:
                    supplier_modes = move.product_id.seller_ids.name.supplier_mode
                    accounts = product_obj.get_product_accounts(cr, uid, move.product_id.product_tmpl_id.id, context)
                    valuation_amount = move.price_unit * move.product_uom_qty
                    account_ids = (supplier_modes == 'Consign_stock_in') and move.product_id.property_account_expense.id \
                            or account_id or move.product_id.property_account_expense.id
                    debit_line_vals = {  
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_uom_qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': picking.name or False,
                        'date': move.date,
                        'partner_id': picking.partner_id and picking.partner_id.id,
                        'credit':  0,
                        'debit':  valuation_amount,
                        'account_id': account_ids,
                    }

                    credit_line_vals = {  
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'quantity': move.product_uom_qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': picking.name or False,
                        'date': move.date,
                        'partner_id': picking.partner_id and picking.partner_id.id,
                        'credit':  valuation_amount,
                        'debit':  0,
                        'account_id': accounts['property_stock_valuation_account_id'],
                    }
                    account_lines.append( (0, 0, credit_line_vals) )
                    account_lines.append( (0, 0, debit_line_vals) )

            account_move_id = move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': account_lines,
                                      'period_id': period_id,
                                      'date': picking.date_done,
                                      'ref': "%s:%s" % (picking.origin or '',  picking.name or '') }, context=context)
            self.write(cr, uid, picking.id, {'account_move_id_out': account_move_id })
            entry_ids.append(account_move_id)
        return entry_ids

class account_invoice_line(osv.osv):
    #print "=======BB=========="
    _inherit = "account.invoice.line"

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = super(account_invoice_line,self).move_line_get(cr, uid, invoice_id, context=context)
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        if inv.type in ('in_invoice','in_refund'):
            for i_line in inv.invoice_line:
                res.extend(self._purchase_move_lines(cr, uid, i_line, res, context=context))
        return res

    def _purchase_move_lines(self, cr, uid, i_line, res, context=None):
        if not i_line.purchase_line_id:
            return []
        inv = i_line.invoice_id
        stock_move_obj = self.pool.get('stock.move')
        decimal_precision = self.pool.get('decimal.precision')
        product_obj = self.pool.get('product.template')
        account_prec = decimal_precision.precision_get(cr, uid, 'Account')
        valuation_stock_move = stock_move_obj.search(cr, uid, [('purchase_line_id', '=', i_line.purchase_line_id.id)], limit=1, context=context)
        if not valuation_stock_move:
            return []
        move = stock_move_obj.browse(cr, uid, valuation_stock_move[0], context=context)
        if not move.picking_id or not move.picking_id.account_move_id:
            return []

        accounts = product_obj.get_product_accounts(cr, uid, i_line.product_id.product_tmpl_id.id, context)
        input_acc = accounts['stock_account_input']
        expense_acc = i_line.product_id.property_account_expense and i_line.product_id.property_account_expense.id

        if not expense_acc:
            expense_acc = i_line.product_id.categ_id.property_account_expense_categ and i_line.product_id.categ_id.property_account_expense_categ.id

        diff_res = []
        for line in res:
            if line.get('invl_id', 0) == i_line.id and expense_acc == line['account_id']:
                line.update({'account_id': input_acc})
                valuation_price_unit = move.price_unit
                price_unit = self.pool['account.tax'].compute_all(cr, uid, line['taxes'], i_line.price_unit * (1-(i_line.discount or 0.0)/100.0), line['quantity'])['total']
                price_line = round(valuation_price_unit * line['quantity'], account_prec)
                price_diff = round(price_unit - price_line, account_prec)

                if abs(price_diff) < 0.001:
                    continue
                line.update({'price': price_line})
                diff_res.append({
                            'type': 'src',
                            'name': i_line.name[:64],
                            'price_unit': round(price_diff / line['quantity'], account_prec),
                            'quantity': line['quantity'],
                            'price': price_diff,
                            'account_id': expense_acc,
                            'product_id': line['product_id'],
                            'uos_id': line['uos_id'],
                            'account_analytic_id': line['account_analytic_id'],
                            'taxes': line.get('taxes', []),
                            })
        return diff_res


class stock_inventory(osv.osv):
    _inherit = 'stock.inventory'

    _columns = {
        'account_move_id': fields.many2one('account.move', u'会计凭证'),
    }

    def create_inventory_entry(self, cr, uid, ids, account_id, period_id, journal_id, context=None):
        """创建盘点会计凭证
        """
        move_obj = self.pool.get('account.move')
        product_obj = self.pool.get('product.template')
        entry_ids = []
        for inventory in self.browse(cr, uid, ids, context=context):
            skip = (inventory.state != 'done') or inventory.account_move_id or (not inventory.move_ids)
            if skip: continue
            
            account_lines = []
            for move in inventory.move_ids:
                for quant in move.quant_ids:
                    valuation_account = quant.product_id.categ_id.property_stock_valuation_account_id.id
                    valuation_amount = quant.cost * quant.qty
                    debit_line_vals = {
                        'name': move.product_id.display_name or move.name,
                        'product_id': quant.product_id.id,
                        'quantity': quant.qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': inventory.name or False,
                        'date': move.date,
                        'credit':  move.location_id.usage != 'inventory' and valuation_amount or 0.0,
                        'debit':  move.location_id.usage == 'inventory' and valuation_amount or 0.0,
                        'account_id': valuation_account,
                    }
                    credit_line_vals = {  
                        'name': move.product_id.display_name or move.name,
                        'product_id': quant.product_id.id,
                        'quantity': quant.qty,
                        'product_uom_id': move.product_uom.id,
                        'ref': inventory.name or False,
                        'date': move.date,
                        'credit': move.location_id.usage == 'inventory' and valuation_amount or 0.0,
                        'debit':  move.location_id.usage != 'inventory' and valuation_amount or 0.0,
                        'account_id': account_id,
                    }
                    account_lines.append( (0, 0, credit_line_vals) )
                    account_lines.append( (0, 0, debit_line_vals) )
            
            account_move_id = move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': account_lines,
                                      'period_id': period_id,
                                      'date': inventory.date,
                                      'ref': 'INV:' + (inventory.name or '')}, context=context)
            self.write(cr, uid, inventory.id, {'account_move_id': account_move_id })
            entry_ids.append(account_move_id)
        return entry_ids

class stock_picking(osv.osv):
    #print "=======AA============"
    _inherit = 'stock.picking'

    def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, moves, inv_type, context=context)
        product_price_unit = {}
        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)

            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
                invoices[key] = invoice_id
            else:
                invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
                merge_vals = {}
                if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
                    invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
                    merge_vals['origin'] = ', '.join(invoice_origin)
                if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
                    invoice_name = filter(None, [invoice.name, invoice_vals['name']])
                    merge_vals['name'] = ', '.join(invoice_name)
                if merge_vals:
                    invoice.write(merge_vals)
            invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
            invoice_line_vals['invoice_id'] = invoices[key]
            invoice_line_vals['origin'] = origin

            if move.product_id.seller_ids.name.supplier_mode == 'Direct_Procurement':
                #expense_acc = i_line.product_id.property_account_expense and i_line.product_id.property_account_expense.id
                invoice_line_vals['account_id'] = move.product_id.categ_id.property_stock_account_input_categ.id
            #if not expense_acc:
            elif move.product_id.seller_ids.name.supplier_mode == 'Consign_stock_in':
                #expense_acc = i_line.product_id.property_account_expense and i_line.product_id.property_account_expense.id
                invoice_line_vals['account_id'] = move.product_id.categ_id.property_stock_account_input_categ.id
            elif move.product_id.seller_ids.name.supplier_mode == 'Consign':
                #expense_acc = i_line.product_id.categ_id.property_account_expense_categ and i_line.product_id.categ_id.property_account_expense_categ.id
                invoice_line_vals['account_id'] = move.product_id.property_account_expense.id
            elif move.product_id.seller_ids.name.supplier_mode == 'Commission':
                invoice_line_vals['account_id'] = move.product_id.categ_id.property_account_expense_categ.id

            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
            if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
                invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
            if is_extra_move[move.id]:
                desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
                    (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
                invoice_line_vals['name'] += ' ' + desc if desc else ''
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
                #the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]

            move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
            move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)

        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()

class ebiz_supplier_account_line(osv.osv):
    #print "============AAA==========="
    _inherit = 'ebiz.supplier.account.line'

    def create_account_invoice(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        no_checked_ids = self.search(cr, uid, [('state','!=','checked'),('id','in',ids)])
        if no_checked_ids:
            raise osv.except_osv((u'警告!'), (u'必须选择已对账的结算项创建供应商发票！'))
        statement_no = 'statement_no'
        for line in self.browse(cr, uid, ids, context=context):
            if statement_no == 'statement_no':
                statement_no = line.statement_no
                state = line.state
                continue
            if state != 'checked':
                raise osv.except_osv((u'警告!'), (u'必须选择已对账的结算项创建供应商发票！'))
            if statement_no != line.statement_no:
                raise osv.except_osv((u'警告!'), (u'只能选择一个对账单创建供应商发票！'))
        cr.execute("""select partner_id,supplier_mode from ebiz_supplier_account_line where id in %s""",(tuple(ids),))
        res_partner = cr.fetchall()
        res_partner = set(res_partner and [(p[0],p[1]) for p in res_partner] or [])
        if len(res_partner) != 1:
            raise osv.except_osv((u'警告!'), (u'请选择同一个供应商的结算项进行创建供应商发票！'))
        res_partner = [p for p in res_partner]
        
        partner = res_partner[0][0]
        partner = self.pool['res.partner'].browse(cr, uid, partner)

        lines = []

        payment_return_ids = self.search(cr, uid, [('type','in',['payment_goods','return_goods']),('id','in',ids)])
        cost_ids = self.search(cr, uid, [('type','=','cost'),('id','in',ids)])
        if partner.supplier_mode == 'Commission':
            if payment_return_ids:
                payment_return_lines = self._prepare_for_invoice_commision(cr, uid, payment_return_ids, context=context)
                lines += payment_return_lines
            if cost_ids:
                cost_lines = self._prepare_for_invoice_cost(cr, uid, cost_ids, context=context)
                lines += cost_lines
        else:
            if payment_return_ids:
                payment_return_lines = self._prepare_for_invoice_goods(cr, uid, payment_return_ids, context=context)
                lines += payment_return_lines
            if cost_ids:
                cost_lines = self._prepare_for_invoice_cost(cr, uid, cost_ids, context=context)
                lines += cost_lines

        journal_id = self.pool.get('account.journal').search(cr, uid, [('type','=','purchase')],)

        #print lines
        for x in lines:
            #print x
            product_ids = x[2]
            product_ids.update({'partner_id': partner.id})
            pro_id = product_ids['product_id']
            acc_id = product_ids['account_id']
            pro_obj = self.pool.get('product.product').browse(cr, uid, pro_id)
            if pro_obj.seller_ids.name.supplier_mode == 'Direct_Procurement':
                product_ids['account_id'] = pro_obj.categ_id.property_stock_account_input_categ.id
                #lines[0][2]['account_id'] = acc_id
                #print acc_id
            elif pro_obj.seller_ids.name.supplier_mode == 'Consign_stock_in':
                product_ids['account_id'] = pro_obj.categ_id.property_stock_account_input_categ.id
                #lines[0][2]['account_id'] = acc_id
                #print acc_id
            elif pro_obj.seller_ids.name.supplier_mode == 'Consign':
                product_ids['account_id'] = pro_obj.property_account_expense.id
                #lines[0][2]['account_id'] = acc_id
                #print acc_id
            elif pro_obj.seller_ids.name.supplier_mode == 'Commission':
                product_ids['account_id'] = pro_obj.categ_id.property_account_expense_categ.id
                #lines[0][2]['account_id'] = acc_id
                #print acc_id
            elif pro_obj.default_code == 'gysbt' and partner.supplier_mode == 'Commission' :
                product_ids['account_id'] = pro_obj.categ_id.property_account_income_categ.id
            elif pro_obj.default_code == 'gysbt' and partner.supplier_mode != 'Commission' :
                product_ids['account_id'] = pro_obj.property_account_income.id
            elif pro_obj.default_code == 'gyskk' and partner.supplier_mode == 'Commission' :
                product_ids['account_id'] = pro_obj.categ_id.property_account_income_categ.id
            elif pro_obj.default_code == 'gyskk' and partner.supplier_mode != 'Commission' :
                product_ids['account_id'] = pro_obj.property_account_income.id

        #print lines

        vals = {
            'type':'in_invoice',
            'state': 'draft',
            'partner_id':partner.id,
            'account_id':partner.property_account_payable and partner.property_account_payable.id or False,
            'journal_id':journal_id and journal_id[0] or 5,
            'date_invoice':time.strftime('%Y-%m-%d'),
            'invoice_line':lines,
            'origin': statement_no,
        }
        invoice_id = self.pool.get('account.invoice').create(cr, uid, vals)
        # 把生成的发票写入到勾选的供应商结算项中，方面数据查询。
        self.write(cr, uid, ids, {'invoice_id':invoice_id, 'state':'settled'})
        return invoice_id

class ebiz_customer_complain(osv.osv):

    _inherit = "ebiz.customer.complain"

    def create_return_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ebiz = self.browse(cr, uid, ids[0], context=context)
        invoice_model = self.pool['account.invoice']
        vals = {}
        invoice_ids = invoice_model.search(cr, uid, [('origin','=',ebiz.name),('type','=','out_refund')])
        #如果退款单已经存在直接跳到退款单form视图
        if invoice_ids:
            return {
                    'res_id': invoice_ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
            } 
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'invoice_form')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']                  
        res = [] 
        if (ebiz.type == 'return_goods'):
            price_unit = 1
            if ebiz.return_amount:
                price_unit = ebiz.return_pay / ebiz.return_amount
            if ebiz.product_id.seller_ids.name.supplier_mode == 'Commission':
            # 'account_id':ebiz.product_id.property_account_income and ebiz.product_id.property_account_income.id or ebiz.product_id.categ_id.property_account_income_categ.id,
                res.append((0,0,{
                    'product_id':ebiz.product_id and ebiz.product_id.id or False,
                    'name':ebiz.product_id and ebiz.product_id.name or '',
                    'price_unit':price_unit,
                    'account_id':ebiz.product_id.categ_id.property_account_income_categ.id,
                    'quantity':ebiz.return_amount,
                    'uos_id': ebiz.product_id.uom_id and ebiz.product_id.uom_id.id or False,
                    }))
            elif ebiz.product_id.seller_ids.name.supplier_mode != 'Commission':
                res.append((0,0,{
                    'product_id':ebiz.product_id and ebiz.product_id.id or False,
                    'name':ebiz.product_id and ebiz.product_id.name or '',
                    'price_unit':price_unit,
                    'account_id':ebiz.product_id.property_account_income and ebiz.product_id.property_account_income.id,
                    'quantity':ebiz.return_amount,
                    'uos_id': ebiz.product_id.uom_id and ebiz.product_id.uom_id.id or False,
                    }))
        else:
            product_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'bysun_customer_complain.ebiz_shop_product_kstk')
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if product_obj:
                if ebiz.product_id.seller_ids.name.supplier_mode == 'Commission':
                #'account_id': product_obj.property_account_income and product_obj.property_account_income.id or product_obj.categ_id.property_account_income_categ.id,
                    res.append((0,0,{
                        'product_id': product_obj.id,
                        'name': product_obj.name,
                        'price_unit': ebiz.return_pay,
                        'account_id': product_obj.categ_id.property_account_income_categ.id,
                        'quantity': 1,
                        'uos_id': product_obj.uom_id and product_obj.uom_id.id or False,
                        }))
                elif ebiz.product_id.seller_ids.name.supplier_mode != 'Commission':
                    res.append((0,0,{
                        'product_id': product_obj.id,
                        'name': product_obj.name,
                        'price_unit': ebiz.return_pay,
                        'account_id': product_obj.property_account_income and product_obj.property_account_income.id,
                        'quantity': 1,
                        'uos_id': product_obj.uom_id and product_obj.uom_id.id or False,
                        }))
        context.update({
            'journal_type': 'sale_refund',
            'type':'out_refund',
            'default_type':'out_refund',
            'default_partner_id':ebiz.order_id and ebiz.order_id.partner_id.id or False,
            })
        default_vals = invoice_model.default_get(cr, uid, ['journal_id'], context=context)
        partner_vals = invoice_model.onchange_partner_id(cr, uid, ids, type='out_refund', \
            partner_id=ebiz.order_id and ebiz.order_id.partner_id.id or False, date_invoice=False, \
            payment_term=False, partner_bank_id=False, company_id=False)['value']
        journal_vals = invoice_model.onchange_journal_id(cr, uid, ids, journal_id=default_vals.get('journal_id',False))['value']
        vals.update(default_vals)
        vals.update(partner_vals)
        vals.update(journal_vals)
        vals.update({
            'type':'out_refund', 
            'partner_id':ebiz.order_id and ebiz.order_id.partner_id.id or False,
            'origin':ebiz.name or '',
            'invoice_line': res,
            })
        _logger.info(vals)
        invoice_id = invoice_model.create(cr, uid, vals, context=context)
        #invoice_model.signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        return {
                'context': context,
                'domain': [('type','=','out_refund')],
                'view_type': 'form',
                'view_mode': 'form',
                'res_id':invoice_id,
                'res_model': 'account.invoice',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
        }

class stock_picking_type(osv.osv):
    _inherit = 'stock.picking.type'

    _columns = {
        'is_create_entry':fields.boolean(u'是否创建会计凭证',default=True),
    }

