import logging

_logger = logging.getLogger(__name__)


# mindbody_gift_card_layout.py

# ============================================
# Prepare Methods
# ============================================

def _prepare_gift_card_layout(self, data):
    """
    Prepare gift card layout values from API response.

    Args:
        data (dict): Gift card layout data from Mindbody API

    Returns:
        dict: Values ready for mindbody.gift.card.layout create/write
    """
    self.ensure_one()

    layout_vals = {
        'layout_id': data.get('LayoutId'),
        'layout_name': data.get('LayoutName'),
        'layout_url': data.get('LayoutUrl'),
    }

    # Remove None values
    layout_vals = {k: v for k, v in layout_vals.items() if v is not None and v is not False}

    return layout_vals

    # mindbody_gift_card_layout.py

    def synchronize(self, from_date=None, to_date=None, limit=None, layout_ids=None):
        """
        Synchronize gift card layouts from Mindbody to Odoo.
        Note: Gift card layouts are typically synced as part of gift card sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            layout_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Gift card layouts are synced automatically during gift card sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
