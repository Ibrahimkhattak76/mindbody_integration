# -*- coding: utf-8 -*-
from odoo import http


class MindbodyWebhookController(http.Controller):
    @http.route('/mindbody/webhook', type='json', auth='public', csrf=False)
    def webhook(self, **payload):
        # Placeholder for webhook handling
        return {'status': 'ok'}
