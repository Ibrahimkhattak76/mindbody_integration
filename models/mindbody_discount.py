import logging

_logger = logging.getLogger(__name__)
# mindbody_discount.py
from odoo import models, fields


class MindbodyDiscount(models.Model):
    _name = 'mindbody.discount'
    _description = 'Mindbody Discount'

    discount_type = fields.Char(string='Type')
    amount = fields.Float(string='Amount')

    # mindbody_discount.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_discount(self, data):
        """
        Prepare discount values from API response.
        
        Args:
            data (dict): Discount data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.discount create/write
        """
        self.ensure_one()

        discount_vals = {
            'discount_type': data.get('Type'),
            'amount': data.get('Amount', 0.0),
        }

        # Remove None values
        discount_vals = {k: v for k, v in discount_vals.items() if v is not None and v is not False}

        return discount_vals

    # mindbody_discount.py

    def synchronize(self, from_date=None, to_date=None, limit=None, discount_ids=None):
        """
        Synchronize discounts from Mindbody to Odoo.
        Note: Discounts are typically synced as part of promo code sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            discount_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Discounts are synced automatically during promo code sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
