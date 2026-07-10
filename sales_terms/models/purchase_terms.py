from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'sale.order'

    terms_and_conditions = fields.Many2one("sale.terms", string="Terms Condition")

    @api.onchange('terms_and_conditions')
    def _onchange_terms_and_conditions(self):
        if self.terms_and_conditions:
            self.note = self.terms_and_conditions.content
        else:
            self.note = False
