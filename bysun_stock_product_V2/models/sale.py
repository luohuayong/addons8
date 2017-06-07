# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'

    logistic_line = fields.One2many('sale.order.logistic', 'order_id', u'物流信息', copy=False, readonly=False)

class sale_order_logistic(models.Model):
    _inherit = 'sale.order.logistic'
    _description = u'订单物流信息'

    name = fields.Selection([ ('print', u'打单'), ('package', u'打包'), ('send', u'出库'), ('signed', u'签收'),], u'物流操作', required=True)
    user_id = fields.Many2one('res.users', string=u"操作员", required=True)
