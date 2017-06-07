# -*- coding: utf-8 -*-

# from openerp import models, fields, api
from openerp.osv import osv, fields, expression
import logging
from datetime import *
import time
_logger = logging.getLogger(__name__)

class stock_quant(osv.osv):
    _inherit ='stock.quant'
    # def _get_remaindays(self,cr, uid, ids,context=None):
    #     res={}
    #     for quant in self.browse(cr, uid, ids, context=context):
    #         life_time=quant.product_id.product_tmpl_id.life_time
    #         batch_code=quant.lot_id.name
    #         if not batch_code:
    #             # 虚拟仓库没有维护批次号，默认给出剩余保质期为 99999
    #             res[quant.id] = 99999
    #         else:
    #             if len(batch_code) > 8:
    #                 remaindays=1
    #                 now = date.today()
    #                 year=int(batch_code[0:4])
    #                 month=int(batch_code[4:6])
    #                 day=int(batch_code[6:8])
    #                 end=date(year,month,day)
    #                 _logger.info('now--end--%s %s',now,end)
    #                 passeddays=(now-end).days
    #                 remaindays=life_time-passeddays
    #                 if remaindays>0:
    #                     remaindays=remaindays
    #                 else:
    #                     remaindays=0
    #                 res[quant.id]=  remaindays
    #             else:
    #                 # 不满足批次号格式
    #                 res[quant.id] = 88888
    #     return res

    _columns = {
        # 'remaindays':fields.function( _get_remaindays ,type='integer',string= u'剩余保质期(天)'),
        'life_time':fields.related('product_id','life_time',type='integer',relation='product.template',string= u'保质期(天)'),
        'remaindays':fields.integer(string= u'剩余保质期(天)'),
        'keep_value_state':fields.selection([
         ('normal', u'正常'),
        ('iscaution', u'已警示'),
        ('isremove', u'可移除'),
        ],string=u'保质期状态',default='normal',readonly=True)
    }

    def _write_remaindays(self,cr, uid,  context=None):
        ids=self.search(cr, uid,[], context=context)
        for quant in self.browse(cr, uid, ids, context=context):
            life_time=quant.product_id.product_tmpl_id.life_time
            batch_code=quant.lot_id.name
            remaindays=0
            if not batch_code:
                remaindays=99999
                keep_value_state='normal'
            else:
                if len(batch_code) > 8:
                    now = date.today()
                    year=int(batch_code[0:4])
                    month=int(batch_code[4:6])
                    day=int(batch_code[6:8])
                    end=date(year,month,day)
                    passeddays=(now-end).days
                    remaindays=life_time-passeddays

                    if life_time!=0 and remaindays>0:
                        remaindays=remaindays
                        if float(remaindays)/ life_time<=1.0/4:
                            keep_value_state='isremove'
                        elif   float(remaindays)/ life_time<=1.0/3 and float(remaindays)/ life_time>1.0/4:
                           keep_value_state='iscaution'
                        else:
                            keep_value_state='normal'
                    else:
                        remaindays=0
                        keep_value_state='isremove'
                else:
                    # 不满足批次号格式
                    remaindays=88888
                    keep_value_state='normal'
            self.write(cr, uid, [quant.id], {'remaindays': remaindays,'keep_value_state':keep_value_state}, context=None)
        return True


