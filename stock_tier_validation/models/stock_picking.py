# Copyright 2019 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ['stock.picking', 'tier.validation']
    _state_from = ['assigned', 'waiting', 'confirmed']
    _state_to = ['done']


    def action_done(self):
        self.write({'state': 'done'})
        res = super().action_done()
        return res

    def _notify_accepted_reviews(self):
        return super(StockPicking, self.sudo())._notify_accepted_reviews()

    def button_validate(self):
        if not self.validated and not self.user_has_groups('stock.group_stock_manager'):
            raise ValidationError('This transfer needs to be validated.')

        res = super().button_validate()
        return res
