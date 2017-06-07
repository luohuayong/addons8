# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)

class check_order_temp(models.TransientModel):
    _name = 'check.order.temp'
    d1=fields.Char(string=u'订单号1')
    d2=fields.Char(string=u'订单号2')
    d3=fields.Char(string=u'订单号3')
    d4=fields.Char(string=u'订单号4')
    d5=fields.Char(string=u'订单号5')
    d6=fields.Char(string=u'订单号6')
    d7=fields.Char(string=u'订单号7')
    d8=fields.Char(string=u'订单号8')
    d9=fields.Char(string=u'订单号9')
    d10=fields.Char(string=u'订单号10')
    d11=fields.Char(string=u'订单号11')
    d12=fields.Char(string=u'订单号12')
    d13=fields.Char(string=u'订单号13')
    d14=fields.Char(string=u'订单号14')
    d15=fields.Char(string=u'订单号15')
    d16=fields.Char(string=u'订单号16')
    d17=fields.Char(string=u'订单号17')
    d18=fields.Char(string=u'订单号18')
    d19=fields.Char(string=u'订单号19')
    d20=fields.Char(string=u'订单号20')

    # 订单审核
    def processing(self,cr, uid, ids, context=None):
        check_obj=self.browse(cr, uid, ids, context=context)
        if check_obj:
            if  check_obj.d1:
                d1=check_obj.d1.replace(' ', '')
                if d1:
                    self.processing_detail(cr, uid, d1, context=None)
            if  check_obj.d2:
                d2=check_obj.d2.replace(' ', '')
                if d2:
                    self.processing_detail(cr, uid, d2, context=None)
            if  check_obj.d3:
                d3=check_obj.d3.replace(' ', '')
                if d3:
                    self.processing_detail(cr, uid, d3, context=None)
            if  check_obj.d4:
                d4=check_obj.d4.replace(' ', '')
                if d4:
                    self.processing_detail(cr, uid, d4, context=None)
            if  check_obj.d5:
                d5=check_obj.d5.replace(' ', '')
                if d5:
                    self.processing_detail(cr, uid, d5, context=None)
            if  check_obj.d6:
                d6=check_obj.d6.replace(' ', '')
                if d6:
                    self.processing_detail(cr, uid, d6, context=None)
            if  check_obj.d7:
                d7=check_obj.d7.replace(' ', '')
                if d7:
                    self.processing_detail(cr, uid, d7, context=None)
            if  check_obj.d8:
                d8=check_obj.d8.replace(' ', '')
                if d8:
                    self.processing_detail(cr, uid, d8, context=None)

            if  check_obj.d9:
                d9=check_obj.d9.replace(' ', '')
                if d9:
                    self.processing_detail(cr, uid, d9, context=None)
            if  check_obj.d10:
                d10=check_obj.d10.replace(' ', '')
                if d10:
                    self.processing_detail(cr, uid, d10, context=None)
            if  check_obj.d11:
                d11=check_obj.d11.replace(' ', '')
                if d11:
                    self.processing_detail(cr, uid, d11, context=None)
            if  check_obj.d12:
                d12=check_obj.d12.replace(' ', '')
                if d12:
                    self.processing_detail(cr, uid, d12, context=None)
            if  check_obj.d13:
                d13=check_obj.d13.replace(' ', '')
                if d13:
                    self.processing_detail(cr, uid, d13, context=None)
            if  check_obj.d14:
                d14=check_obj.d14.replace(' ', '')
                if d14:
                    self.processing_detail(cr, uid, d14, context=None)
            if  check_obj.d15:
                d15=check_obj.d15.replace(' ', '')
                if d15:
                    self.processing_detail(cr, uid, d15, context=None)
            if  check_obj.d16:
                d16=check_obj.d16.replace(' ', '')
                if d16:
                    self.processing_detail(cr, uid, d16, context=None)
            if  check_obj.d17:
                d17=check_obj.d17.replace(' ', '')
                if d17:
                    self.processing_detail(cr, uid, d17, context=None)
            if  check_obj.d18:
                d18=check_obj.d18.replace(' ', '')
                if d18:
                    self.processing_detail(cr, uid, d18, context=None)
            if  check_obj.d19:
                d19=check_obj.d19.replace(' ', '')
                if d19:
                    self.processing_detail(cr, uid, d19, context=None)
            if  check_obj.d20:
                d20=check_obj.d20.replace(' ', '')
                if d20:
                    self.processing_detail(cr, uid, d20, context=None)
        return True


    def processcancel(self,cr, uid, ids, context=None):
        check_obj=self.browse(cr, uid, ids, context=context)
        if check_obj:
            if  check_obj.d1:
                d1=check_obj.d1.replace(' ', '')
                _logger.info(d1)
                if d1:
                    self.processing_cancel(cr, uid, d1, context=None)
            if  check_obj.d2:
                d2=check_obj.d2.replace(' ', '')
                if d2:
                    self.processing_cancel(cr, uid, d2, context=None)
            if  check_obj.d3:
                d3=check_obj.d3.replace(' ', '')
                if d3:
                    self.processing_cancel(cr, uid, d3, context=None)
            if  check_obj.d4:
                d4=check_obj.d4.replace(' ', '')
                if d4:
                    self.processing_cancel(cr, uid, d4, context=None)
            if  check_obj.d5:
                d5=check_obj.d5.replace(' ', '')
                if d5:
                    self.processing_cancel(cr, uid, d5, context=None)
            if  check_obj.d6:
                d6=check_obj.d6.replace(' ', '')
                if d6:
                    self.processing_cancel(cr, uid, d6, context=None)
            if  check_obj.d7:
                d7=check_obj.d7.replace(' ', '')
                if d7:
                    self.processing_cancel(cr, uid, d7, context=None)
            if  check_obj.d8:
                d8=check_obj.d8.replace(' ', '')
                if d8:
                    self.processing_cancel(cr, uid, d8, context=None)

            if  check_obj.d9:
                d9=check_obj.d9.replace(' ', '')
                if d9:
                    self.processing_cancel(cr, uid, d9, context=None)
            if  check_obj.d10:
                d10=check_obj.d10.replace(' ', '')
                if d10:
                    self.processing_cancel(cr, uid, d10, context=None)
            if  check_obj.d11:
                d11=check_obj.d11.replace(' ', '')
                if d11:
                    self.processing_cancel(cr, uid, d11, context=None)
            if  check_obj.d12:
                d12=check_obj.d12.replace(' ', '')
                if d12:
                    self.processing_cancel(cr, uid, d12, context=None)
            if  check_obj.d13:
                d13=check_obj.d13.replace(' ', '')
                if d13:
                    self.processing_cancel(cr, uid, d13, context=None)
            if  check_obj.d14:
                d14=check_obj.d14.replace(' ', '')
                if d14:
                    self.processing_cancel(cr, uid, d14, context=None)
            if  check_obj.d15:
                d15=check_obj.d15.replace(' ', '')
                if d15:
                    self.processing_cancel(cr, uid, d15, context=None)
            if  check_obj.d16:
                d16=check_obj.d16.replace(' ', '')
                if d16:
                    self.processing_cancel(cr, uid, d16, context=None)
            if  check_obj.d17:
                d17=check_obj.d17.replace(' ', '')
                if d17:
                    self.processing_cancel(cr, uid, d17, context=None)
            if  check_obj.d18:
                d18=check_obj.d18.replace(' ', '')
                if d18:
                    self.processing_cancel(cr, uid, d18, context=None)
            if  check_obj.d19:
                d19=check_obj.d19.replace(' ', '')
                if d19:
                    self.processing_cancel(cr, uid, d19, context=None)
            if  check_obj.d20:
                d20=check_obj.d20.replace(' ', '')
                if d20:
                    self.processing_cancel(cr, uid, d20, context=None)
        return True


    # 订单取消
    def processing_cancel(self,cr, uid, d, context=None):
        if len(d)>0:
            order_obj=self.pool['sale.order']
            ods=order_obj.search(cr, uid,[('name','ilike',d)], context=context)
            _logger.info(ods)
            if ods:
                for od in order_obj.browse(cr, uid, ods, context=context):
                    _logger.info(od.id)
                    if  od.shipped:
                        _logger.info('------------shipped----')
                        continue
                    else:
                        order_obj.action_cancel(cr, uid, [od.id], context=None)
            else:
                _logger.info('------------guo----')
        return True

    # 订单审核
    def processing_detail(self,cr, uid, d, context=None):
        if len(d)>0:
            order_obj=self.pool['sale.order']
            ods=order_obj.search(cr, uid,[('name','ilike',d)], context=context)
            _logger.info(ods)
            if ods:
                order_obj=self.pool['sale.order']
                for od in order_obj.browse(cr, uid, ods, context=context):
                    if od.state=='draft':
                        order_obj.action_button_confirm(cr, uid, [od.id], context=None)
                    elif od.state=='manual' and  od.pending:
                        order_obj.action_suspend(cr, uid, [od.id], context=None)
                    else:
                        _logger.info('------------guo----')
            else:
                _logger.info('------------guo----')
        else:
            _logger.info('------------guo----')
        return True

    # 税率设置   小规模 17% 3%
    def supplier_tax3(self,cr, uid, ids, context=None):
        query="""
        select pt.id,rp.supplier_mode  from product_template  pt
                    left join   product_supplierinfo  ps on pt.id=ps.product_tmpl_id
                    left join res_partner  rp on rp.id=ps.name
                    where rp.active=True and rp.is_company=True and  rp.supplier=True and rp.taxtype='commission'
        """
        cr.execute(query)
        data = cr.fetchall()
        if data:
            for row in data:
                pid=row[0]
                if row[1]=='Commission':
                    insertsql="""
                    insert into product_taxes_rel  (tax_id,prod_id) values (6,%s);
                    insert into product_supplier_taxes_rel  (tax_id,prod_id) values (10,%s);
                    """
                    cr.execute(insertsql,([pid,pid]))
                elif  row[1] in ('Consign','Consign_stock_in'):
                    insertsql="""
                    insert into product_taxes_rel  (tax_id,prod_id) values (1,%s);
                    insert into product_supplier_taxes_rel  (tax_id,prod_id) values (2,%s);
                    """
                    cr.execute(insertsql,([pid,pid]))
                else:
                    continue
            return True
    # 税率设置   小规模 17% 3%
    def supplier_tax2(self,cr, uid, ids, context=None):
        query="""select pt.id  from product_template  pt
                    left join   product_supplierinfo  ps on pt.id=ps.product_tmpl_id
                    left join res_partner  rp on rp.id=ps.name
                    where rp.name in (
                    '山东青未了电子商务有限公司',
                    '凤凰食佰汇电子商务有限公司',
                    '烟台宏信投资有限公司'
                    )"""
        cr.execute(query)
        data = cr.fetchall()
        if data:
            for row in data:
                pid=row[0]
                insertsql="""
                    insert into product_taxes_rel  (tax_id,prod_id) values (1,%s);
                    insert into product_supplier_taxes_rel  (tax_id,prod_id) values (9,%s);
                    """
                cr.execute(insertsql,([pid,pid]))
        return True

    # 税率设置  一般纳税人 17% 13%
    def supplier_tax1(self,cr, uid, ids, context=None):
        query="""select pt.id  from product_template  pt
                    left join   product_supplierinfo  ps on pt.id=ps.product_tmpl_id
                    left join res_partner  rp on rp.id=ps.name
                    where rp.name in (
                    '安国市佰花堂商贸有限公司',
                    '湖北九珠蛋业有限公司',
                    '湖北鑫龙吉国际物流有限公司',
                    '武汉红日子食品有限公司',
                    '襄阳赛亚米业有限公司',
                    '宜昌市花艳粮食储备库'
                    )"""
        cr.execute(query)
        data = cr.fetchall()
        if data:
            for row in data:
                pid=row[0]
                insertsql="""
                    insert into product_taxes_rel  (tax_id,prod_id) values (1,%s);
                    insert into product_supplier_taxes_rel  (tax_id,prod_id) values (4,%s);
                    """
                cr.execute(insertsql,([pid,pid]))
        return True
    # 税率设置  一般纳税人 17% 17%
    def supplier_tax(self,cr, uid, ids, context=None):
        query="""select pt.id  from product_template  pt
                    left join   product_supplierinfo  ps on pt.id=ps.product_tmpl_id
                    left join res_partner  rp on rp.id=ps.name
                    where rp.name in (
                    '安国市佰花堂商贸有限公司',
                    '北京华康易达商贸有限公司',
                    '北京麻小仙营销有限公司',
                    '北京微熏餐饮管理有限公司',
                    '北京众有得国际贸易有限公司',
                    '常州本兮食品有限公司',
                    '大连海朴生物科技有限公司',
                    '福建大用生态农业综合发展有限公司',
                    '广西卓上农业科技股份有限公司',
                    '韩进（上海）食品有限公司',
                    '湖北华丽食品股份有限公司',
                    '湖北九珠蛋业有限公司',
                    '湖北鑫龙吉国际物流有限公司',
                    '江西颖川堂绿色食品有限公司',
                    '晋华和佐（厦门）食品股份有限公司',
                    '满洲里双实肉类食品有限公司',
                    '南京双诺企业管理有限公司',
                    '上海金百岁农庄食品有限公司',
                    '上海来又来实业有限公司',
                    '上海树品贸易有限公司',
                    '天津泰德丰进出口有限公司',
                    '威海市牧耘贸易有限公司',
                    '武汉昌久源商贸有限责任公司（代销入仓）',
                    '武汉楚台缘贸易有限公司',
                    '武汉广诚卓越贸易有限公司',
                    '武汉赫氏柏生物科技有限公司',
                    '武汉红日子食品有限公司',
                    '武汉利永兴商贸有限公司',
                    '武汉市海隆丰商贸有限公司',
                    '武汉万邦惠通贸易有限公司',
                    '武汉香满园食品有限公司',
                    '武汉亿美康国际贸易有限公司',
                    '武汉亿信工贸有限公司',
                    '襄阳赛亚米业有限公司',
                    '宜昌市花艳粮食储备库',
                    '宜都土老憨电子商务有限公司',
                    '北京永嘉商贸有限公司',
                    '恩施市峰顶农产品有限责任公司',
                    '苏州淘豆食品有限公司',
                    '湖北卧龙神厨食品股份有限公司',
                    '杭州西厨贝可电子商务有限公司',
                    '深圳市榴芒一刻餐饮管理有限公司',
                    '武汉恒升益商贸有限公司',
                    '武汉市卓雨菲商贸有限公司',
                    '武汉金瑞琪贸易有限公司',
                    '青岛企顾署企业服务有限责任公司',
                    '青岛企顾署企业服务有限公司(进口)',
                    '宁波吉量贸易有限公司',
                    '北京明大天润商贸有限公司',
                    '东莞市联收食品有限公司',
                    '鑫磊博览城有限公司',
                    '南京松拓食品有限公司',
                    '珠海唯他可可饮料有限公司',
                    '武汉海裕达商贸有限公司',
                    '东强国际贸易（北京）有限公司',
                    '利川市柏杨康美食品有限公司',
                    '四川省放牛娃食品有限公司',
                    '恩施市楚丰现代农业有限公司',
                    '上海品其投资发展有限公司',
                    '杭州群飞乐享生态农业有限公司',
                    '湖北屈姑国际农业集团屈姑商贸有限公司（休闲零食）',
                    '郧西便民牛羊养殖专业合作社'
                    ) """
        cr.execute(query)
        data = cr.fetchall()
        if data:
            for row in data:
                pid=row[0]
                insertsql="""
                    insert into product_taxes_rel  (tax_id,prod_id) values (1,%s);
                    insert into product_supplier_taxes_rel  (tax_id,prod_id) values (2,%s);
                    """
                cr.execute(insertsql,([pid,pid]))
        return True


    def init_purchaseprice(self,cr,uid,ids,context=None):
        _logger.info('__________________')
        _logger.info(self.pool['product.template'].browse(cr, uid, ids, context=context))
        pobj=self.pool['product.template']

        ids=pobj.search(cr, uid,[], context=context)

        for pt in self.pool['product.template'].browse(cr, uid, ids,context=context):
            # _logger.info(pt.name)
            pt.update({
            'purchase_price': pt.standard_price
        })
        return True