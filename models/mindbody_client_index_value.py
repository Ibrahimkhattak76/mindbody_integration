import logging

_logger = logging.getLogger(__name__)
# mindbody_client_index_value.py
from odoo import models, fields


class MindbodyClientIndexValue(models.Model):
    _name = 'mindbody.client.index.value'
    _description = 'Mindbody Client Index Value'

    client_index_id = fields.Many2one('mindbody.client.index', string='Client Index')
    client_id = fields.Many2one('mindbody.client', string='Client')

    value_id = fields.Integer(string='Value ID')
    active = fields.Boolean(string='Active')
    name = fields.Char(string='Name')

    # mindbody_client_index_value.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_index_value(self, data):
        """
        Prepare client index value from API response.
        
        Args:
            data (dict): Client index value data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.index.value create/write
        """
        self.ensure_one()

        # Handle both standalone value data and nested from client
        value_vals = {
            'value_id': data.get('ValueId') or data.get('Id'),
            'active': data.get('Active', True),
            'name': data.get('Name'),
        }

        # If this is from a client, we also have the index ID
        if data.get('Id') and not data.get('ValueId'):
            value_vals['client_index_id'] = data.get('Id')

        # Remove None values
        value_vals = {k: v for k, v in value_vals.items() if v is not None and v is not False}

        return value_vals

    # mindbody_client_index_value.py

    def synchronize(self, from_date=None, to_date=None, limit=None, index_value_ids=None):
        """
        Synchronize client index values from Mindbody to Odoo.
        Note: Client index values are typically synced as part of client index sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            index_value_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Client index values are synced automatically during client index sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
