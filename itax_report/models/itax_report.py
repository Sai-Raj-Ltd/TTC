# -*- coding: utf-8 -*-
##############################################################################
# Part of Corensult Solutions. (Website: www.corensultsolutions.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_flag = fields.Selection([('import', 'IMPORT'), ('local', 'LOCAL')], string='Customer Flag')
    
class AccountMove(models.Model):
    _inherit = "account.move"

    custom_entry_number = fields.Char('Custom Entry Number')
