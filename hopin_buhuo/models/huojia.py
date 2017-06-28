# -*- coding:utf-8 -*-
from openerp import models, fields, api
from datetime import datetime
import math


class huojia_item(models.Model):
    _name = 'buhuo.huojia_item'

    warehouse_id = fields.Many2one('stock.warehouse', string=u"货架编号",readonly=True)
    product_id = fields.Many2one('product.product', string=u"商品编号",readonly=True)
    product_code = fields.Char(related='product_id.product_tmpl_id.t_guid', string=u"商品编码", readonly=True)
    product_name = fields.Char(related='product_id.name_template', string=u"商品名称", readonly=True)

    kucun = fields.Integer(string=u"当前库存",readonly=True)
    shuliang = fields.Integer(string=u"最后补货数量",readonly=True)
    zhuangtai = fields.Selection([('0', u"-"), ('1', u"正常"), ('2', u"待补货"), ('3', u"紧急补货")],
                                 string=u"状态提醒", compute='_zhuangtai',readonly=True)

    @api.depends('kucun', 'shuliang')
    def _zhuangtai(self):
        for r in self:
            # if not r.kucun or not r.shuliang:
            if r.kucun is None or r.shuliang is None:
                r.zhuangtai = '0'
            elif r.kucun == 0:
                r.zhuangtai = '3'
            elif r.shuliang == 0:
                r.zhuangtai = '0'
            elif float(r.kucun)/float(r.shuliang) > 0.5:
                r.zhuangtai = '1'
            elif float(r.kucun)/float(r.shuliang) > 0.3:
                r.zhuangtai = '2'
            else:
                r.zhuangtai = '3'

    @api.multi
    def kucun_and_buhuo_jisuan(self):

        # 删除货架商品项
        huojia_items = self.env['buhuo.huojia_item'].search([])
        huojia_items.unlink()

        # 货架列表
        huojia_warehouse = self.env['stock.warehouse'].search([['code', 'like', 'Q%']])
        for warehouse in huojia_warehouse:
            # 货架商品库存总量
            sql = """
                SELECT SUM(qty) as sum_qty
                FROM stock_quant
                WHERE location_id = %s
            """
            self.env.cr.execute(sql, ([warehouse.lot_stock_id.id]))
            sum_qty = self.env.cr.fetchall()
            warehouse.buhuo_kucun = sum_qty[0][0]
            # 货架最后一个完成状态的补货单
            sql = """
                SELECT p.id,sum_qty,p.name,p.state,p.create_date,p.date_done
                FROM
                (SELECT picking_id,sum(product_uom_qty) AS sum_qty
                FROM stock_move
                WHERE location_id = 12 AND location_dest_id = %s AND state = 'done'
                GROUP BY picking_id) m 
                LEFT JOIN stock_picking p 
                ON m.picking_id = p.id
                ORDER BY p.date_done DESC
                LIMIT 1
            """
            self.env.cr.execute(sql, ([warehouse.lot_stock_id.id]))
            buhuo_jilu = self.env.cr.fetchall()
            if len(buhuo_jilu) == 1:
                warehouse.buhuo_shuliang = buhuo_jilu[0][1]

            # 货架库存商品分组合计
            sql = """
                SELECT product_id,SUM(qty) as sum_qty
                FROM stock_quant
                WHERE location_id = %s
                GROUP BY product_id
            """
            self.env.cr.execute(sql, ([warehouse.lot_stock_id.id]))
            huojia_item_sum = self.env.cr.fetchall()
            for item in huojia_item_sum:
                huojia_items.create({
                    'warehouse_id': warehouse.id,
                    'product_id': item[0],
                    'kucun': item[1],
                    'shuliang': 0,
                })

            # 货架最后补货商品分组合计
            if len(buhuo_jilu) == 1:
                sql = """
                    SELECT product_id,sum(product_uom_qty) AS sum_qty
                    FROM stock_move
                    WHERE picking_id = %s
                    GROUP BY product_id
                """
                self.env.cr.execute(sql, ([buhuo_jilu[0][0]]))
                buhuo_item_sum = self.env.cr.fetchall()

                # 判断是否存在对应货架库存
                # 存在，更新最后补货数量
                # 不存在，插入货架库存商品分组合计
                for item in buhuo_item_sum:
                    item_temp = huojia_items.search([['warehouse_id', '=', warehouse.id],
                                                     ['product_id', '=', item[0]]])
                    if len(item_temp) == 0:
                        huojia_items.create({
                            'warehouse_id': warehouse.id,
                            'product_id': item[0],
                            'kucun': 0,
                            'shuliang': item[1]
                        })
                    else:
                        item_temp[0].shuliang = item[1]

# class xiaoshou(models.Model):
#     _name = 'buhuo.xiaoshou'
#     date = fields.Date(string=u"日期",readonly=True)
#     warehouse_id = fields.Many2one('stock.warehouse', string=u"货架ID",readonly=True)
#     warehouse_code = fields.Char(related='warehouse_id.code', string=u"货架编号", readonly=True)
#     warehouse_address = fields.Many2one(related='warehouse_id.partner_id', string=u"货架地址", readonly=True)
#     xiaoliang = fields.Integer(string=u"销量",readonly=True)
#     jine = fields.Float(digits=(6, 2), string=u"金额",readonly=True)
#     item_ids = fields.One2many('buhuo.xiaoshou_item', 'xiaoshou_id', string=u"销售项")


class xiaoshou_item(models.Model):
    _name = 'buhuo.xiaoshou_item'
    date = fields.Date(string=u"日期", readonly=True)

    warehouse_id = fields.Many2one('stock.warehouse', string=u"货架ID", readonly=True)
    warehouse_code = fields.Char(related='warehouse_id.code', string=u"货架编号", readonly=True)
    warehouse_address = fields.Many2one(related='warehouse_id.partner_id', string=u"货架地址", readonly=True)
    warehouse_buhuo_qiyong = fields.Boolean(related='warehouse_id.buhuo_qiyong', string=u"启用", readonly=True)

    product_id = fields.Many2one('product.product', string=u"商品ID", readonly=True)
    product_code = fields.Char(related='product_id.product_tmpl_id.t_guid', string=u"商品编码", readonly=True)
    product_name = fields.Char(related='product_id.name_template', string=u"商品名称", readonly=True)

    xiaoliang = fields.Integer(string=u"销量", readonly=True)
    jine = fields.Float(digits=(6, 2), string=u"金额", readonly=True)
    # xiaoshou_id = fields.Many2one('buhuo.xiaoshou',string=u"销售编号")

    @api.multi
    def xiaoshou_jisuan(self):
        xiaoshou_data_old = self.env['buhuo.xiaoshou_item'].search([])
        xiaoshou_data_old.unlink()

        # 日期-货架-商品分组统计
        sql = """
            SELECT date_order,warehouse_id,product_id,SUM(product_uom_qty) AS qty,SUM(line_total) AS total
            FROM
            (SELECT id,code
            FROM stock_warehouse
            WHERE code LIKE 'Q%') w
            LEFT JOIN
            (SELECT warehouse_id,id,to_char(date_order,'yyyy-mm-dd') AS date_order
            FROM sale_order
            WHERE date_order < current_date
            AND date_order > current_date - interval '3 month') o 
            ON w.id = o.warehouse_id
            LEFT JOIN
            (SELECT order_id,product_id,product_uom_qty,(product_uom_qty * price_unit) AS line_total
            FROM sale_order_line) ol
            ON o.id = ol.order_id
            WHERE date_order IS NOT NULL AND product_uom_qty IS NOT NULL AND line_total IS NOT NULL
            GROUP BY date_order,warehouse_id,product_id
        """
        self.env.cr.execute(sql)
        xiaoshou_set = self.env.cr.fetchall()

        for i, xiaoshou_record in enumerate(xiaoshou_set):
            self.env['buhuo.xiaoshou_item'].create({
                'date': xiaoshou_record[0],
                'warehouse_id': xiaoshou_record[1],
                'product_id': xiaoshou_record[2],
                'xiaoliang': xiaoshou_record[3],
                'jine': xiaoshou_record[4],
            })

class buhuo_wizard(models.Model):
    _name = 'buhuo.buhuo_wizard'

    @api.multi
    def create_buhuodan(self):
        location_src_id = 12
        # 需要补货货架
        sql = """
            SELECT id,lot_stock_id,buhuo_zhouqi,code
            FROM stock_warehouse
            WHERE code like 'Q%'
            AND current_date - buhuo_riqi > buhuo_zhouqi
            AND buhuo_qiyong = TRUE
        """
        self.env.cr.execute(sql)
        huojia_warehouse = self.env.cr.fetchall()

        # 分拣类型集合（源位置为大仓）
        stock_picking_type_set = self.env['stock.picking.type']\
            .search([['default_location_src_id', '=', location_src_id]])

        # 调拨单集合（状态为草稿）
        stock_picking_set = self.env['stock.picking']\
            .search([['state', '=', 'draft']])

        # 按货架生成补货单
        for warehouse in huojia_warehouse:
            warehouse_id = warehouse[0]
            location_id = warehouse[1]
            buhuo_zhouqi = int(warehouse[2])
            code = warehouse[3]

            # 货架对应分拣类型
            # stock_picking_type = stock_picking_type_set \
            #     .search([['default_location_dest_id', '=', location_id]])
            stock_picking_type = stock_picking_type_set.filtered(
                lambda x: x.default_location_dest_id.id == location_id)

            # 对应补货单
            # stock_picking_record = stock_picking_set \
            #     .search([['picking_type_id', '=', stock_picking_type[0].id]])
            stock_picking_record = stock_picking_set.filtered(
                lambda x: x.picking_type_id.id == stock_picking_type[0].id)

            # 生成补货单或删除补货单明细
            if len(stock_picking_record) == 0:
                name = '{0}JL{1}SYS'.format(code, datetime.now().strftime('%Y%m%d%H%M%S'))
                stock_picking_record = stock_picking_record.create({
                    'state': 'draft',
                    'name': name,
                    'picking_type_id': stock_picking_type[0].id,
                    # 'priority': 1,
                    # 'move_type': 'direct',
                    # 'company_id': 1,
                    # 'date': datetime.utcnow(),
                    # 'recompute_pack_op': True,
                    # 'return_no': '',
                    # 'return_send': False,
                    # 'invoice_state': 'none',
                    # 'reception_to_invoice': False,
                    # 'weight_uom_id': 3,
                    # 'weight': 0,
                    # 'weight_net': 0,
                    # 'infact_weight': 0,
                    # 'number_of_packages': 0,
                    # 'pending': False,
                    # 'customer_signed': False,
                })
            else:
                self.env['stock.move'] \
                    .search([['picking_id', '=', stock_picking_record[0].id]])\
                    .unlink()

            # 货架商品列表
            sql = """
                SELECT w.product_id,w.qty_kucun,s.qty_xiaoshou_avg30,
                t.name,t.uom_id
                FROM
                (SELECT product_id,SUM(qty) as qty_kucun
                FROM stock_quant
                WHERE location_id = %s
                GROUP BY product_id) w
                INNER JOIN
                (SELECT product_id,SUM(product_uom_qty) / 30 AS qty_xiaoshou_avg30
                FROM
                (SELECT id,warehouse_id
                FROM sale_order
                WHERE date_order < current_date
                AND date_order >= current_date - INTERVAL '30 day'
                AND warehouse_id = %s) o
                LEFT JOIN
                (SELECT order_id,product_id,product_uom_qty
                FROM sale_order_line) ol
                ON o.id = ol.order_id
                GROUP BY product_id) s
                ON w.product_id = s.product_id
                LEFT JOIN product_product p
                ON w.product_id = p.id
                LEFT JOIN product_template t
                ON p.product_tmpl_id = t.id
            """
        self.env.cr.execute(sql, ([location_id, warehouse_id]))
        product_set = self.env.cr.fetchall()

        for product_item in product_set:
            product_id = product_item[0]
            kucun = int(product_item[1])
            xiaoshou_avg30 = float(product_item[2])
            product_name = product_item[3]
            product_uom = product_item[4]
            xiaoshou_avg30_zhouqi = math.ceil(xiaoshou_avg30 * buhuo_zhouqi * 1.3)
            if kucun < xiaoshou_avg30_zhouqi:
                buhuo_qty = xiaoshou_avg30_zhouqi - kucun
                self.env['stock.move'].create({
                    'product_uos_qty': buhuo_qty,
                    'product_uom': product_uom,
                    'product_uom_qty': buhuo_qty,
                    # 'product_qty': buhuo_qty,
                    # 'company_id': '1',
                    # 'date': datetime.utcnow(),
                    'location_id': location_src_id,
                    # 'priority': 1,
                    'state': 'draft',
                    'date_expected': datetime.utcnow(),
                    'name': product_name,
                    # 'partially_available': False,
                    # 'propagate': True,
                    # 'procure_method': 'make_to_stock',
                    'product_id': product_id,
                    'location_dest_id': location_id,
                    'picking_type_id': stock_picking_type[0].id,
                    'picking_id': stock_picking_record[0].id,
                    # 'invoice_state': 'none',
                    # 'weight_uom_id': 3,
                    # 'weight': 0,
                    # 'weight_net': 0,
                    # 'is_import_supplier_account': False,
                    # 'valuation': 0,
                })










