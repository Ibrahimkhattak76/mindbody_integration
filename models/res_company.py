# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    mindbody_enabled = fields.Boolean("Mindbody Integration")
    # Core API credentials
    mindbody_api_key = fields.Char("Mindbody API Key")
    mindbody_site_id = fields.Char("Mindbody Site ID")

    # Staff credentials (for /usertoken/issue)
    mindbody_username = fields.Char("Mindbody Username")
    mindbody_password = fields.Char("Mindbody Password")

    # Token storage
    mindbody_access_token = fields.Char("Mindbody Access Token")
    mindbody_token_expires_at = fields.Datetime("Token Expiry")

    # Optional behavior fields
    mindbody_auto_sync = fields.Boolean("Enable Automatic Sync")
    mindbody_sync_interval = fields.Integer(
        "Sync Interval (minutes)", default=30
    )

    # -----------------------------
    # Test Mindbody API Connection
    # -----------------------------
    def test_mindbody_connection(self):
        """
        Tests connection to Mindbody API for the current company.

        Steps:
        1. Ensures Mindbody integration is enabled for this company.
        2. Initializes API service instance.
        3. Ensures valid token (issues new one if expired/missing).
        4. Makes a simple test call to fetch a few classes.
        5. Prints response for inspection or confirms connection.

        Example successful output:
        {
            'PaginationResponse': {'RequestedLimit': 5, 'RequestedOffset': 0, 'PageSize': 5, 'TotalResults': 7},
            'Classes': [
                {
                    'ClassScheduleId': 2143,
                    'Name': 'Bottoms Up',
                    'StartDateTime': '2026-03-04T09:15:00',
                    'EndDateTime': '2026-03-04T10:15:00',
                    'Staff': [{'Id': 100000237, 'FirstName': 'Dan', 'LastName': 'Darragh'}],
                    'Location': {'Name': 'Clubville', 'Address': '4051 S Broad St, San Luis Obispo, CA 93401'},
                    'MaxCapacity': 30,
                    'TotalBooked': 0,
                },
                {
                    'ClassScheduleId': 2152,
                    'Name': 'Yoga',
                    'StartDateTime': '2026-03-04T06:20:00',
                    'EndDateTime': '2026-03-04T07:20:00',
                    'Staff': [{'Id': 100000259, 'FirstName': 'Jake', 'LastName': 'Hay'}],
                    'Location': {'Name': 'Personal Training Upper Studio'},
                    'MaxCapacity': 20,
                    'TotalBooked': 1,
                }
            ]
        }
        """
        self.ensure_one()
        if not self.mindbody_enabled:
            raise UserError(_("Mindbody integration is not enabled for this company."))
        # payroll_commissions waseem commissions
        try:
            # Initialize API instance scoped to this company
            api = self.env['mindbody.api'].with_company(self)

            # Ensure valid authentication token
            api._ensure_token()

            # Test call: fetch up to 5 classes
            classes = api.call_endpoint("sale_products")
            if classes:
                # Print response for dev inspection
                print("Fetched classes:", classes)
            else:
                print("Mindbody connection successful. No classes returned.")

        except UserError as e:
            raise UserError(_("Mindbody connection test failed: %s") % e)
        except Exception as e:
            _logger.exception("Unexpected error during Mindbody connection test")
            raise UserError(_("Unexpected error: %s") % e)
