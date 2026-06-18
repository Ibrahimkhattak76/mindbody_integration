import logging

_logger = logging.getLogger(__name__)
# mindbody_client_type.py
from odoo import models, fields


class MindbodyClientType(models.Model):
    _name = 'mindbody.client.type'
    _description = 'Mindbody Client Type'

    client_type_id = fields.Integer(string='Client Type ID')
    name = fields.Char(string='Name')

    # mindbody_client_type.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_type(self, data):
        """
        Prepare client type values from API response.
        
        Args:
            data (dict): Client type data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.type create/write
        """
        self.ensure_one()

        client_type_vals = {
            'client_type_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        client_type_vals = {k: v for k, v in client_type_vals.items() if v is not None and v is not False}

        return client_type_vals

    # mindbody_client_type.py

    def synchronize(self, from_date=None, to_date=None, limit=None, client_type_ids=None):
        """
        Synchronize client types from Mindbody to Odoo.
        Note: Client types are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            client_type_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Client types are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
