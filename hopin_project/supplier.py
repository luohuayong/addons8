# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.exceptions import ValidationError
import datetime
import logging

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    shipfee=fields.Float(u'邮费',default=0)
    buyer=fields.Many2one('res.users',u'采销员')
    buyerassistant=fields.Many2one('res.users',u'采销助理')
    taxtype=fields.Selection([
        ('general',u'一般纳税人'),
        ('littlescope',u'小规模纳税人'),
        ('business',u'个体工商'),
        ('commission',u'佣金')],string=u'税率类型',default='commission')

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                if name:
                    namelist=name.split(',')
                    if len(namelist)==2:
                        name=namelist[1]
                    else:
                        name=namelist[0]
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

class supplier_fee(models.TransientModel):
    _name='supplier.fee'

    starttime=fields.Datetime(u'开始时间', required=True, default=lambda self: fields.Datetime.now())
    endtime=fields.Datetime(u'结束时间', required=True, default=lambda self: fields.Datetime.now())


    def ebiz_supplier_fee_wizard(self ,cr, uid, ids, context=None):
        """计算供应商邮费，针对 佣金 和代售不入仓 """
        if context:
            supplier_ids=context['active_ids']
            supplier_fee_obj=self.browse(cr, uid, ids, context)
            if supplier_fee_obj:
                query="""select count(*)  from  sale_order so
                        right join
                        (
                        select sol1.order_id,max(rp.id) as supplierid,max(rp.name) as suppliername from  sale_order_line sol1
                        left join product_product pp1 on pp1.id=sol1.product_id
                        left join product_template pt1 on pt1.id=pp1.product_tmpl_id
                        left join  product_supplierinfo ps on pt1.id=ps.product_tmpl_id
                        left join res_partner rp on rp.id=ps.name
                        left join  stock_warehouse sw on rp.stock_warehouse_id=sw.id
                        where pt1.type!='service'  and  rp.supplier_mode in ('Consign','Commission')
                        group by sol1.order_id
                        ) yh on yh.order_id=so.id
                        left join
                        (
                        select sm.origin,max(sm.date) as date  from  stock_move  sm
                        left join stock_picking_type spt on spt.id = sm.picking_type_id
                        left join stock_picking sp on sp.id=sm.picking_id
                        left join  product_product pp on  sm.product_id=pp.id
                        where sm.state='done' and spt.code='outgoing'
                        group by sm.origin
                        ) move on move.origin=so.name

                        where so.state not in ('draft','cancel')  and move.date>=%s  and move.date<=%s  and yh.supplierid=%s
                         """
                suppliers=self.pool['res.partner'].browse(cr, uid, supplier_ids, context)
                ErrorStr=''
                for supplier in suppliers:
                    if supplier.shipfee<=0:
                        ErrorStr=ErrorStr+supplier.name+','
                _logger.info(ErrorStr)
                if  ErrorStr:
                    raise  ValidationError(u'请先维护邮费:'+ErrorStr)
                for supplier in suppliers:
                    if supplier.supplier_mode in ('Consign','Commission'):
                        cr.execute(query,([supplier_fee_obj.starttime, supplier_fee_obj.endtime, supplier.id]))
                        data = cr.fetchall()
                        if data:
                            fee_count=data[0][0]
                            if fee_count==0:
                                continue
                            fee_tatol=fee_count*supplier.shipfee
                            notes=u'总共有'+str(fee_count)+u'笔订单,每笔订单邮费是'+str(supplier.shipfee)+u'元,总计'+str(fee_tatol)+u'元'
                            _logger.info(notes)
                            product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bysun_supplier_account', 'ebiz_shop_product_supplier_gysbt')
                            if product_id:
                                product_id = product_id[1]
                            vals = {
                                'partner_id': supplier.id ,
                                'product_id': product_id,
                                'uom_id':  1,
                                'amount': 1,
                                'type':  'cost',
                                'commission':0,
                                'state': 'draft',
                                'standard_price':fee_tatol,
                                'notes':notes,
                                'supplier_mode': supplier.supplier_mode,
                                'qty_send': supplier_fee_obj.endtime,
                            }
                            self.pool['ebiz.supplier.account.line'].create(cr, uid, vals,context)
                    else:
                        continue
        return True