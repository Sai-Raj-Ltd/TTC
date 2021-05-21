# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Low'), ('2','Medium'), ('3', 'High')], 'Priority', default='0', index=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, change_default=True, tracking=True, domain="[('status','=','Done')]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    type = fields.Selection(
        [('Stock Item', 'Stock Item'), ('CAPEX', 'CAPEX'), ('OPEX','OPEX')], default='Stock Item', index=True)
    
    
    
    @api.onchange('order_line')
    def get_product_type(self):
        type_loc=''
        for rec in self.order_line:
            if type_loc not in ['CAPEX','OPEX']:
                type_loc=rec.type
        self.type=type_loc
        
        
        
    
    
    @api.onchange('partner_id')
    def get_warning(self):
        warning = {}
        result = {}
        if self.partner_id.rating=='0':
            records = self.env['res.partner'].search([('rating', 'in', ['1','2','3']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
        if self.partner_id.rating=='1':
            records = self.env['res.partner'].search([('rating', 'in', ['2','3']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
        if self.partner_id.rating=='2':
            records = self.env['res.partner'].search([('rating', 'in', ['3']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
                
                
                


    
    
class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    
    status = fields.Selection(
        [('Draft', 'Draft'), ('Done', 'Done')], 'Status', default='Draft', index=True)
    rating = fields.Selection(
        [('0', 'Normal'), ('1', 'Low'), ('2','Medium'), ('3', 'High')], 'Rating', default='0', index=True)

    
    def make_checker(self):
        self.status='Done'
class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    
    rating = fields.Selection(
        [('0', 'Normal'), ('1', 'Low'), ('2','Medium'), ('3', 'High')], 'Rating', default='0', index=True)
    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    type = fields.Selection(
        [('Stock Item', 'Stock Item'), ('CAPEX', 'CAPEX'), ('OPEX','OPEX')], default='Stock Item', index=True)
