# -*- coding: utf-8 -*-
from odoo import models, fields


class ManualSyncWizard(models.TransientModel):
    _name = 'mindbody.manual.sync'
    _description = 'Manual Sync Wizard'

    sync_type = fields.Selection([('clients', 'Clients'), ('classes', 'Classes'), ('bookings', 'Bookings')],
                                 required=True)

    def sync_now(self):
        # Placeholder for manual sync logic
        pass
