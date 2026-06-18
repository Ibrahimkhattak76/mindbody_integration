import logging

_logger = logging.getLogger(__name__)
# mindbody_promo_applicable_item.py
from odoo import models, fields


class MindbodyPromoApplicableItem(models.Model):
    _name = 'mindbody.promo.applicable.item'
    _description = 'Mindbody Promo Applicable Item'

    promo_code_id = fields.Many2one('mindbody.promo.code', string='Promo Code')

    item_type = fields.Char(string='Type')
    item_id = fields.Integer(string='ID')
    name = fields.Char(string='Name')

    # mindbody_promo_applicable_item.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_promo_applicable_item(self, data):
        """
        Prepare promo applicable item values from API response.
        
        Args:
            data (dict): Promo applicable item data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.promo.applicable.item create/write
        """
        self.ensure_one()

        item_vals = {
            'item_type': data.get('Type'),
            'item_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        item_vals = {k: v for k, v in item_vals.items() if v is not None and v is not False}

        return item_vals

    # mindbody_promo_applicable_item.py

    def synchronize(self, from_date=None, to_date=None, limit=None, applicable_item_ids=None):
        """
        Synchronize promo applicable items from Mindbody to Odoo.
        Note: Promo applicable items are typically synced as part of promo code sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            applicable_item_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Promo applicable items are synced automatically during promo code sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
