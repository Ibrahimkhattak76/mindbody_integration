import logging

_logger = logging.getLogger(__name__)
# mindbody_price.py
from odoo import models, fields


class MindbodyPrice(models.Model):
    _name = 'mindbody.price'
    _description = 'Mindbody Price'

    total = fields.Float(string='Total')
    sub_total = fields.Float(string='Sub Total')
    discount = fields.Float(string='Discount')
    tax = fields.Float(string='Tax')

    # mindbody_price.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_price(self, data):
        """
        Prepare price values from API response.
        
        Args:
            data (dict): Price data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.price create/write
        """
        self.ensure_one()

        price_vals = {
            'total': data.get('Total', 0.0),
            'sub_total': data.get('SubTotal', 0.0),
            'discount': data.get('Discount', 0.0),
            'tax': data.get('Tax', 0.0),
        }

        # Remove None values
        price_vals = {k: v for k, v in price_vals.items() if v is not None and v is not False}

        return price_vals

    # mindbody_price.py

    def synchronize(self, from_date=None, to_date=None, limit=None, price_ids=None):
        """
        Synchronize prices from Mindbody to Odoo.
        Note: Prices are typically synced as part of product/service sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            price_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Prices are synced automatically during product/service sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
