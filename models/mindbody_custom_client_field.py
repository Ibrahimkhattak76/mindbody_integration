import logging

_logger = logging.getLogger(__name__)
# mindbody_custom_client_field.py
from odoo import models, fields


class MindbodyCustomClientField(models.Model):
    _name = 'mindbody.custom.client.field'
    _description = 'Mindbody Custom Client Field'

    client_id = fields.Many2one('mindbody.client', string='Client')

    custom_field_id = fields.Integer(string='Custom Field ID')
    value = fields.Char(string='Value')
    data_type = fields.Char(string='Data Type')
    name = fields.Char(string='Name')

    # mindbody_custom_client_field.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_custom_client_field(self, data):
        """
        Prepare custom client field values from API response.
        
        Args:
            data (dict): Custom client field data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.custom.client.field create/write
        """
        self.ensure_one()

        custom_field_vals = {
            'custom_field_id': data.get('Id'),
            'value': data.get('Value'),
            'data_type': data.get('DataType'),
            'name': data.get('Name'),
        }

        # Remove None values
        custom_field_vals = {k: v for k, v in custom_field_vals.items() if v is not None and v is not False}

        return custom_field_vals

    # mindbody_custom_client_field.py

    def synchronize(self, from_date=None, to_date=None, limit=None, custom_field_ids=None):
        """
        Synchronize custom client fields from Mindbody to Odoo.
        Note: Custom client fields are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            custom_field_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Custom client fields are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
