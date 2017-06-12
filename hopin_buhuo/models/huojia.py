# -*- coding:utf-8 -*-
from openerp import models, fields, api
from datetime import datetime


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

    product_id = fields.Many2one('product.product', string=u"商品ID", readonly=True)
    product_code = fields.Char(related='product_id.product_tmpl_id.t_guid', string=u"商品编码", readonly=True)
    product_name = fields.Char(related='product_id.name_template', string=u"商品名称", readonly=True)

    xiaoliang = fields.Integer(string=u"销量", readonly=True)
    jine = fields.Float(digits=(6, 2), string=u"金额", readonly=True)
    # xiaoshou_id = fields.Many2one('buhuo.xiaoshou',string=u"销售编号")

    @api.multi
    def xiaoshou_jisuan(self):
        # 删除向导产生的空数据
        xiaoshou_items_null = self.env['buhuo.xiaoshou_item'].search([['date', '=', False]])
        xiaoshou_items_null.unlink()

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
            WHERE date_order < current_date) o 
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
        # xiaoshou_data_old = self.env['buhuo.xiaoshou'].search([])
        for i, xiaoshou_record in enumerate(xiaoshou_set):
            xiaoshou_record_temp = self.env['buhuo.xiaoshou_item'].\
                search([['date', '=', xiaoshou_record[0]],
                        ['warehouse_id', '=', xiaoshou_record[1]],
                        ['product_id', '=', xiaoshou_record[2]]])
            if len(xiaoshou_record_temp) == 0:
                self.env['buhuo.xiaoshou_item'].create({
                    'date': xiaoshou_record[0],
                    'warehouse_id': xiaoshou_record[1],
                    'product_id': xiaoshou_record[2],
                    'xiaoliang': xiaoshou_record[3],
                    'jine': xiaoshou_record[4],
                })

                # # 商品销售分组统计
                # sql = """
                #     SELECT product_id,SUM(product_uom_qty) AS qty,
                #     SUM(line_total)/SUM(product_uom_qty) AS price,
                #     SUM(line_total) AS total
                #     FROM
                #     (SELECT id
                #     FROM sale_order
                #     WHERE to_char(date_order,'yyyy-mm-dd') = '2016-10-25'
                #     AND warehouse_id = 321) o
                #     LEFT JOIN
                #     (SELECT order_id,product_id,product_uom_qty,(product_uom_qty * price_unit) AS line_total
                #     FROM sale_order_line) ol
                #     ON o.id = ol.order_id
                #     GROUP BY product_id
                # """
                # self.env.cr.execute(sql,([xiaoshou_record[0],xiaoshou_record[1]]))
                # xiaoshou_item_set = self.env.cr.fetchall()
                # # xiaoshou_item_old = self.env['buhuo.xiaoshou_item'].search([])
                # # xiaoshou_old = self.env['buhuo.xiaoshou'].search([])
                # for xiaoshou_item_record in xiaoshou_item_set:
                #     self.env['buhuo.xiaoshou_item'].create({
                #         'product_id': xiaoshou_item_record[0],
                #         'xiaoliang': xiaoshou_item_record[1],
                #         'danjia': xiaoshou_item_record[2],
                #         'jine': xiaoshou_item_record[3],
                #         'xiaoshou_id': xiaoshou_record_temp.id,
                #     })
            # xiaoshou_temp = self.env['buhuo.xiaoshou'].\
            #     search([['date','=',item[0]],
            #             ['warehouse_id','=',item[1]]])
            # if len(xiaoshou_temp) == 0:
            #     global xiaoshou_temp
            #     xiaoshou_temp = self.env['buhuo.xiaoshou'].create({
            #         'date': item[0],
            #         'warehouse_id': item[1],
            #         # 'xiaoliang': item[2],
            #         # 'jine': item[3],
            # #     })
            # xiaoshou_item_temp = self.env['buhuo.xiaoshou_item'].\
            #     search([['xiaoshou_id','=',xiaoshou_temp.id],
            #             ['product_id','=',item[2]]])
            # if len(xiaoshou_item_temp) == 0:
            #     self.env['buhuo.xiaoshou_item'].create({
            #         'product_id': item[2],
            #         'xiaoliang': item[3],
            #         # 'danjia': item[2],
            #         'jine': item[4],
            #         'xiaoshou_id': xiaoshou_temp.id,
            #     })
            # elif xiaoshou_item_temp.xiaoliang != item[3]:
            #     xiaoshou_item_temp.xiaoliang = item[3]
            #     xiaoshou_item_temp.jine = item[4]

# class huojia_jisuan(models.TransientModel):
#     _name = 'buhuo.huojia_jisuan'








