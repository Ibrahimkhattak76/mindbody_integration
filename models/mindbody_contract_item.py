import logging

_logger = logging.getLogger(__name__)
# mindbody_contract_item.py
from odoo import models, fields


class MindbodyContractItem(models.Model):
    _name = 'mindbody.contract.item'
    _description = 'Mindbody Contract Item'

    contract_id = fields.Many2one('mindbody.contract', string='Contract')
    item_id = fields.Char(string='Item ID')
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    item_type = fields.Char(string='Type')
    price = fields.Float(string='Price')
    quantity = fields.Float(string='Quantity')
    one_time_item = fields.Boolean(string='One Time Item')

    # mindbody_contract_item.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contract_item(self, data):
        """
        Prepare contract item values from API response.
        
        Args:
            data (dict): Contract item data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.contract.item create/write
        """
        self.ensure_one()

        contract_item_vals = {
            'item_id': data.get('Id'),
            'name': data.get('Name'),
            'description': data.get('Description'),
            'item_type': data.get('Type'),
            'price': data.get('Price', 0.0),
            'quantity': data.get('Quantity', 0.0),
            'one_time_item': data.get('OneTimeItem', False),
        }

        # Remove None values
        contract_item_vals = {k: v for k, v in contract_item_vals.items() if v is not None and v is not False}

        return contract_item_vals

    # mindbody_contract_item.py

    def synchronize(self, from_date=None, to_date=None, limit=None, contract_item_ids=None):
        """
        Synchronize contract items from Mindbody to Odoo.
        Note: Contract items are typically synced as part of contract sync.
        This method is for standalone sync if needed.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            contract_item_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Contract items are synced automatically during contract sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
