# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Related to company
    mindbody_enabled = fields.Boolean(related="company_id.mindbody_enabled", readonly=False)
    mindbody_api_key = fields.Char("Mindbody API Key", related="company_id.mindbody_api_key", readonly=False)
    mindbody_site_id = fields.Char("Mindbody Site ID", related="company_id.mindbody_site_id", readonly=False)

    mindbody_username = fields.Char("Mindbody Username", related="company_id.mindbody_username", readonly=False)
    mindbody_password = fields.Char("Mindbody Password", related="company_id.mindbody_password", readonly=False)

    mindbody_access_token = fields.Char(related="company_id.mindbody_access_token", readonly=False)
    mindbody_token_expires_at = fields.Datetime(related="company_id.mindbody_token_expires_at", readonly=False)

    mindbody_auto_sync = fields.Boolean("Enable Automatic Sync", related="company_id.mindbody_auto_sync",
                                        readonly=False)
    mindbody_sync_interval = fields.Integer(related="company_id.mindbody_sync_interval", readonly=False)
