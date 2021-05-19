# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseExtended(http.Controller):
#     @http.route('/purchase_extended/purchase_extended/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_extended/purchase_extended/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_extended.listing', {
#             'root': '/purchase_extended/purchase_extended',
#             'objects': http.request.env['purchase_extended.purchase_extended'].search([]),
#         })

#     @http.route('/purchase_extended/purchase_extended/objects/<model("purchase_extended.purchase_extended"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_extended.object', {
#             'object': obj
#         })