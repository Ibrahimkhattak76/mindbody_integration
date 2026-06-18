import logging

_logger = logging.getLogger(__name__)
# mindbody_product_size.py
from odoo import models, fields


class MindbodyProductSize(models.Model):
    _name = 'mindbody.product.size'
    _description = 'Mindbody Product Size'

    size_id = fields.Integer(string='Size ID')
    name = fields.Char(string='Name')

    # mindbody_product_size.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_product_size(self, data):
        """
        Prepare product size values from API response.
        
        Args:
            data (dict): Product size data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.product.size create/write
        """

        size_vals = {
            'size_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        size_vals = {k: v for k, v in size_vals.items() if v is not None and v is not False}

        return size_vals

    def get_size(self, data):
        if not data:
            return False
        vals = self._prepare_product_size(data)
        rec = self.search([('size_id', '=', vals.get('size_id', 0))], limit=1)
        return self.create([vals]) if not rec else rec

    def synchronize(self, from_date=None, to_date=None, limit=None, size_ids=None):
        """
        Synchronize product sizes from Mindbody to Odoo.
        Note: Product sizes are typically synced as part of product sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            size_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Product sizes are synced automatically during product sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
