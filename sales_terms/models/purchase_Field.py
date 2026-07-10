from odoo import models, fields


class PurchaseTerms(models.Model):
    _name = "sale.terms"
    _description = "Terms and Conditions"

    name = fields.Char(string="Name", required=True)
    content = fields.Html(string="Content")
