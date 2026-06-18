import logging

_logger = logging.getLogger(__name__)
# mindbody_purchase_totals.py
from odoo import models, fields


class MindbodyPurchaseTotals(models.Model):
    _name = 'mindbody.purchase.totals'
    _description = 'Mindbody Purchase Totals'

    purchase_id = fields.Many2one('mindbody.purchase.contract.status', string='Purchase')

    total = fields.Float(string='Total')
    sub_total = fields.Float(string='Sub Total')
    discount = fields.Float(string='Discount')
    tax = fields.Float(string='Tax')

    # mindbody_purchase_totals.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_purchase_totals(self, data):
        """
        Prepare purchase totals values from API response.
        
        Args:
            data (dict): Purchase totals data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.purchase.totals create/write
        """
        self.ensure_one()

        totals_vals = {
            'total': data.get('Total', 0.0),
            'sub_total': data.get('SubTotal', 0.0),
            'discount': data.get('Discount', 0.0),
            'tax': data.get('Tax', 0.0),
        }

        # Remove None values
        totals_vals = {k: v for k, v in totals_vals.items() if v is not None and v is not False}

        return totals_vals

    # mindbody_purchase_totals.py

    def synchronize(self, from_date=None, to_date=None, limit=None, totals_ids=None):
        """
        Synchronize purchase totals from Mindbody to Odoo.
        Note: Purchase totals are typically synced as part of purchase contract status sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            totals_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Purchase totals are synced automatically during purchase contract status sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
