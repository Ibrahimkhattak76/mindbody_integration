# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mindbody_id = fields.Integer(index=True)
    mindbody_last_sync = fields.Datetime()
