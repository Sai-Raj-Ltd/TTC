# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare
from email.utils import formataddr


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
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('validated', 'Validated'),
        ('approved', 'Approved'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)    
    
    
    def button_validate(self):
        self.state='validated'
    def button_approved(self):
        self.state='approved'
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent','approved']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True
    
    
    @api.onchange('order_line')
    def get_product_type(self):
        type_loc=''
        for rec in self.order_line:
            if type_loc not in ['CAPEX','OPEX']:
                type_loc=rec.type
        self.type=type_loc 
    
#     @api.onchange('partner_id')
#     def get_warning(self):
#         warning = {}
#         result = {}
#         if self.partner_id.rating=='3':
#             records = self.env['res.partner'].search([('rating', 'in', ['1','2','0']),('status', '=', 'Done')])
#             if records:
#                 warning = {
#                         'title': ('Alert!'),
#                         'message': ('There exists a vendor with higher rating'),
#                     }
#                 if warning:
#                     result['warning'] = warning
#                     return result
#         if self.partner_id.rating=='2':
#             records = self.env['res.partner'].search([('rating', 'in', ['1','0']),('status', '=', 'Done')])
#             if records:
#                 warning = {
#                         'title': ('Alert!'),
#                         'message': ('There exists a vendor with higher rating'),
#                     }
#                 if warning:
#                     result['warning'] = warning
#                     return result
#         if self.partner_id.rating=='1':
#             records = self.env['res.partner'].search([('rating', 'in', ['0']),('status', '=', 'Done')])
#             if records:
#                 warning = {
#                         'title': ('Alert!'),
#                         'message': ('There exists a vendor with higher rating'),
#                     }
#                 if warning:
#                     result['warning'] = warning
#                     return result
                
   
    
class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    
    status = fields.Selection(
        [('Draft', 'Draft'), ('Done', 'Done')], 'Status', default='Draft', index=True)
    rating = fields.Selection(
        [('3', 'Normal'), ('2', 'Low'), ('1','Medium'), ('0', 'High')], 'Rating', default='3', index=True)

    
    def make_checker(self):
        self.status='Done'
class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    
    rating = fields.Selection(
        [('0', 'Normal'), ('1', 'Low'), ('2','Medium'), ('3', 'High')], 'Rating', default='0', index=True)
    
    def send_remainder(self):
        template = self.env.ref('purchase_extended.send_reminder_mail')
        mail = self.env['mail.mail'].create({
             'subject':'Set Rating for Products reminder',
            'body_html': 'Please set reting for unrated products',
            'email_to':  [formataddr((partner.display_name,partner.login)) for partner in self.env.ref('purchase.group_purchase_manager').users]
        })
        mail.send()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    type = fields.Selection(
        [('Stock Item', 'Stock Item'), ('CAPEX', 'CAPEX'), ('OPEX','OPEX')], default='Stock Item', index=True)

class ProductProduct(models.Model):
    _inherit = "product.product"    
    
    def _prepare_sellers(self, params=False):
        return self.seller_ids.filtered(lambda s: s.name.active).sorted(lambda s: (s.name.rating,s.sequence, -s.min_qty, s.price, s.id))

    
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self._prepare_sellers(params)
        sellers = sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.env.company.id)
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != self:
                continue
            if not res or res.name == seller.name:
                res |= seller
        return res.sorted(lambda s: s.name.rating)

    
class AccountMove(models.Model):
    _inherit = "account.move"
    
    is_credit = fields.Boolean(compute="_get_credit_note")
    approved = fields.Boolean(default=False)
    
    
    def _get_credit_note(self):
        for rec in self:
            if self.env['account.move'].search([  ('partner_id', '=', rec.partner_id.id),
            ('move_type', '=', 'in_refund'),
            ('payment_state', '!=', 'paid')]):
                rec.is_credit=False
            else:
                rec.is_credit=True
            
    def get_approve(self):
        self.approved=True    

        
class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"
    
    name = fields.Many2one(
        'res.partner', 'Vendor',
        ondelete='cascade', required=True,
        help="Vendor of this product", domain="[('status','=','Done')]", check_company=True)

    @api.onchange('name')
    def _onchange_name(self):
        self.currency_id = self.name.property_purchase_currency_id.id or self.env.company.currency_id.id
        warning = {}
        result = {}
        if self.name.rating=='3':
            records = self.env['res.partner'].search([('rating', 'in', ['1','2','0']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
        if self.name.rating=='2':
            records = self.env['res.partner'].search([('rating', 'in', ['1','0']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
        if self.name.rating=='1':
            records = self.env['res.partner'].search([('rating', 'in', ['0']),('status', '=', 'Done')])
            if records:
                warning = {
                        'title': ('Alert!'),
                        'message': ('There exists a vendor with higher rating'),
                    }
                if warning:
                    result['warning'] = warning
                    return result
