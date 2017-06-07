# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 CCI Connect asbl (http://www.cciconnect.be) All Rights Reserved.
#                       Philmer <philmer@cciconnect.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{
    'name': 'Ebiz Customer Complain (客诉)',
    'version': '1.0',
    'author': 'Odoo',
    'category': 'Customer Complain',
    'website': 'https://www.odoo.com/page/accounting',
    'description': """
    """,
    'depends': ['base','bysun_stock_product','bysun_supplier_account','account_voucher','bysun_picking','delivery'],
    'init_xml': [ ],
    'update_xml': [
        'security/ir.model.access.csv',
        'ebiz_customer_complain_seq.xml',
        'ebiz_customer_complain_view.xml',
        'ebiz_customer_complain_action.xml',
        'ebiz_customer_complain_data.xml',
        ],
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
