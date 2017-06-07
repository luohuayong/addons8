# -*- coding: utf-8 -*-

import calendar
import datetime

from openerp import api, fields, models, _


class StockReportQuant(models.TransientModel):
    _name = 'stock.report.quant'

    def _get_first_date(self):
        now = datetime.datetime.now()
        # set the date to the first day of the month
        return datetime.datetime(now.year, now.month, 1)

    def _get_last_date(self):
        now = datetime.datetime.now()
        # return value [first_day, last_day]
        month_range = calendar.monthrange(now.year, now.month)

        # set the date to the end day of the month
        return datetime.datetime(now.year, now.month, month_range[1])

    def _default_stock_location(self):
        try:
            warehouse = self.env.ref("stock.warehouse0")

            return warehouse.lot_stock_id.id
        except:
            return False

    location_id = fields.Many2one(
        'stock.location', string=u'库位', required=True,
        default=_default_stock_location)

    start_date = fields.Date(
        u'起始日期', required=True, default=_get_first_date)
    end_date = fields.Date(
        u'结束日期', required=True, default=_get_last_date)

    @api.multi
    def print_report(self):
        ctx = {
            'location': self.location_id and self.location_id.id or False,
            'from_date': self.start_date,
            'to_date': self.end_date,
            'check_duration_qty': True,
        }

        tree = self.env.ref('report_stock_cn.view_product_product_tree')
        graph = self.env.ref('report_stock_cn.view_product_product_graph')
        # search = self.env.ref('report_stock_cn.view_product_search')

        return {
            'name': u'库存月报(%s - %s)' % (self.start_date, self.end_date),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'views': [(graph.id, 'graph'), (tree.id, 'tree')],
            # 'search_view_id': (search.id, u'search'),
            'context': ctx,
            'domain': [('type', '=', 'product'), ('active', '=', True)]
        }
