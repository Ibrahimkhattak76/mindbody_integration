import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyWaitlistInfo(models.Model):
    _name = 'mindbody.waitlist.info'
    _description = 'Mindbody Waitlist Info'

    client_id = fields.Many2one('mindbody.client', string='Client')

    waitlist_id = fields.Integer(string='Waitlist ID')
    waitlist_order_number = fields.Integer(string='Waitlist Order Number')

    # mindbody_waitlist_info.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_waitlist_info(self, data):
        """
        Prepare waitlist info values from API response.
        
        Args:
            data (dict): Waitlist info data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.waitlist.info create/write
        """
        # self.ensure_one()

        waitlist_info_vals = {
            'waitlist_id': data.get('WaitlistId'),
            'waitlist_order_number': data.get('WaitlistOrderNumber', 0),
        }

        # Remove None values
        waitlist_info_vals = {k: v for k, v in waitlist_info_vals.items() if v is not None and v is not False}

        return waitlist_info_vals

    # mindbody_waitlist_info.py

    def synchronize(self, from_date=None, to_date=None, limit=None, waitlist_info_ids=None):
        """
        Synchronize waitlist info from Mindbody to Odoo.
        Note: Waitlist info is typically synced as part of client schedule sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            waitlist_info_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Waitlist info is synced automatically during client schedule sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
