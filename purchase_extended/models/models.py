# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Low'), ('2','Medium'), ('3', 'High')], 'Priority', default='0', index=True)
    
    
class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    
    status = fields.Selection(
        [('Maker', 'Maker'), ('Checker', 'Checker')], 'Status', default='Maker', index=True)
    
    def make_checker(self):
        self.status='Checker'
