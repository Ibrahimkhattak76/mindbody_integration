import logging

_logger = logging.getLogger(__name__)
# mindbody_client_class.py
from odoo import models, fields


class MindbodyClientClass(models.Model):
    _name = 'mindbody.client.class'
    _description = 'Mindbody Client Class'

    client_id = fields.Many2one('mindbody.client', string='Client')
    class_instance_id = fields.Many2one('mindbody.class.instance', string='Class Instance')

    # For add client to class response
    visit_id_ref = fields.Many2one('mindbody.class.visit', string='Visit')

    # mindbody_client_class.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_class(self, data):
        """
        Prepare client class values from API response.
        
        Args:
            data (dict): Client class data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.class create/write
        """
        self.ensure_one()

        client_class_vals = {}

        # Add Many2one fields with create commands will be handled by caller
        # This is a thin wrapper since client_class is typically a mapping table

        # Remove None values
        client_class_vals = {k: v for k, v in client_class_vals.items() if v is not None and v is not False}

        return client_class_vals

    # mindbody_client_class.py

    def synchronize(self, from_date=None, to_date=None, limit=None, client_class_ids=None):
        """
        Synchronize client class associations from Mindbody to Odoo.
        Note: Client class associations are typically synced as part of class instance sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            client_class_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Client class associations are synced automatically during class instance sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
