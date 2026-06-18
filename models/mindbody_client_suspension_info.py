import logging

_logger = logging.getLogger(__name__)
# mindbody_client_suspension_info.py
from odoo import models, fields


class MindbodyClientSuspensionInfo(models.Model):
    _name = 'mindbody.client.suspension.info'
    _description = 'Mindbody Client Suspension Information'

    client_id = fields.Many2one('mindbody.client', string='Client')

    booking_suspended = fields.Boolean(string='Booking Suspended')
    suspension_start_date = fields.Char(string='Suspension Start Date')
    suspension_end_date = fields.Char(string='Suspension End Date')

    # mindbody_client_suspension_info.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_suspension_info(self, data):
        """
        Prepare suspension info values from API response.
        
        Args:
            data (dict): Suspension info data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.suspension.info create/write
        """
        self.ensure_one()

        suspension_vals = {
            'booking_suspended': data.get('BookingSuspended', False),
            'suspension_start_date': data.get('SuspensionStartDate'),
            'suspension_end_date': data.get('SuspensionEndDate'),
        }

        # Remove None values
        suspension_vals = {k: v for k, v in suspension_vals.items() if v is not None and v is not False}

        return suspension_vals

    # mindbody_client_suspension_info.py

    def synchronize(self, from_date=None, to_date=None, limit=None, suspension_info_ids=None):
        """
        Synchronize client suspension info from Mindbody to Odoo.
        Note: Suspension info is typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            suspension_info_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Suspension info is synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
