import logging

_logger = logging.getLogger(__name__)
# mindbody_product_color.py
from odoo import models, fields


class MindbodyProductColor(models.Model):
    _name = 'mindbody.product.color'
    _description = 'Mindbody Product Color'

    color_id = fields.Integer(string='Color ID')
    name = fields.Char(string='Name')

    # mindbody_product_color.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_product_color(self, data):
        """
        Prepare product color values from API response.
        
        Args:
            data (dict): Product color data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.product.color create/write
        """

        color_vals = {
            'color_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        color_vals = {k: v for k, v in color_vals.items() if v is not None and v is not False}

        return color_vals

    def get_color(self, color_data):
        if not color_data:
            return False

        vals = self._prepare_product_color(color_data)
        color = self.search([('color_id', '=', vals.get('color_id', 0))], limit=1)
        return self.create(vals) if not color else color

    def synchronize(self, from_date=None, to_date=None, limit=None, color_ids=None):
        """
        Synchronize product colors from Mindbody to Odoo.
        Note: Product colors are typically synced as part of product sync.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            color_ids (list, optional): Not used for this endpoint

        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Product colors are synced automatically during product sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
