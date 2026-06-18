import logging

_logger = logging.getLogger(__name__)
# mindbody_liability.py
from odoo import models, fields


class MindbodyLiability(models.Model):
    _name = 'mindbody.liability'
    _description = 'Mindbody Liability'

    client_id = fields.Many2one('mindbody.client', string='Client')

    agreement_date = fields.Datetime(string='Agreement Date')
    is_released = fields.Boolean(string='Is Released')
    released_by = fields.Integer(string='Released By')

    liability_release = fields.Boolean(string='Liability Release')

    # mindbody_liability.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_liability(self, liability_data, liability_release):
        """
        Prepare liability values from API response.
        
        Args:
            liability_data (dict): Liability data from API
            liability_release (bool): Liability release flag
            
        Returns:
            dict: Values ready for mindbody.liability create/write
        """
        self.ensure_one()

        if not liability_data and not liability_release:
            return None

        liability_vals = {
            'agreement_date': liability_data.get('AgreementDate') if liability_data else None,
            'is_released': liability_data.get('IsReleased', False) if liability_data else False,
            'released_by': liability_data.get('ReleasedBy') if liability_data else None,
            'liability_release': liability_release or False,
        }

        # Remove None values
        liability_vals = {k: v for k, v in liability_vals.items() if v is not None and v is not False}

        return liability_vals

    # mindbody_liability.py

    def synchronize(self, from_date=None, to_date=None, limit=None, liability_ids=None):
        """
        Synchronize liabilities from Mindbody to Odoo.
        Note: Liabilities are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            liability_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Liabilities are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
