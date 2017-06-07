# -*- coding: utf-8 -*-
from openerp import http

# class HopinExcel(http.Controller):
#     @http.route('/hopin_excel/hopin_excel/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hopin_excel/hopin_excel/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hopin_excel.listing', {
#             'root': '/hopin_excel/hopin_excel',
#             'objects': http.request.env['hopin_excel.hopin_excel'].search([]),
#         })

#     @http.route('/hopin_excel/hopin_excel/objects/<model("hopin_excel.hopin_excel"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hopin_excel.object', {
#             'object': obj
#         })