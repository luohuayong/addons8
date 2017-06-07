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
    'name': 'Ebiz Supplier Account',
    'version': '1.0',
    'author': 'Odoo',
    'category': 'Supplier Account',
    'website': 'https://www.odoo.com/page/accounting',
    'description': """
    """,
    'depends': ['base','product','stock','sale','purchase','account','bysun_stock_product_V2','sale_stock','bysun_picking_V2'],
    'init_xml': [ ],
    'update_xml': [
        'wizard/ebiz_supplier_account_make_view.xml',
        'wizard/ebiz_supplier_account_create_view.xml',
        'security/ir.model.access.csv',
        'ebiz_supplier_account_seq.xml',
        'ebiz_supplier_account_view.xml',
        'ebiz_supplier_account_action.xml',
        'ebiz_supplier_account_data_view.xml',
        ],
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
