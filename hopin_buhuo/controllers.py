# -*- coding: utf-8 -*-
from openerp import http

# class HopinBuhuo(http.Controller):
#     @http.route('/hopin_buhuo/hopin_buhuo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hopin_buhuo/hopin_buhuo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hopin_buhuo.listing', {
#             'root': '/hopin_buhuo/hopin_buhuo',
#             'objects': http.request.env['hopin_buhuo.hopin_buhuo'].search([]),
#         })

#     @http.route('/hopin_buhuo/hopin_buhuo/objects/<model("hopin_buhuo.hopin_buhuo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hopin_buhuo.object', {
#             'object': obj
#         })