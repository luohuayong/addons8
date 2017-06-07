# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, osv
import logging


class sale_order(models.Model):
    _inherit = 'sale.order'

    def action_button_confirm(self, cr, uid, ids, context=None):
        for so in self.browse(cr, uid, ids, context=context):
            if (so.pending):
                raise exceptions.ValidationError((u"订单 %s 已挂起!") % (so.name))
        return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)