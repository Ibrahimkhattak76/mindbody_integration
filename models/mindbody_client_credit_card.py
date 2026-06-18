import logging

_logger = logging.getLogger(__name__)
# mindbody_client_credit_card.py
from odoo import models, fields


class MindbodyClientCreditCard(models.Model):
    _name = 'mindbody.client.credit.card'
    _description = 'Mindbody Client Credit Card'

    client_id = fields.Many2one('mindbody.client', string='Client')

    address = fields.Char(string='Address')
    card_holder = fields.Char(string='Card Holder')
    card_number = fields.Char(string='Card Number')
    card_type = fields.Char(string='Card Type')
    city = fields.Char(string='City')
    exp_month = fields.Char(string='Exp Month')
    exp_year = fields.Char(string='Exp Year')
    last_four = fields.Char(string='Last Four')
    postal_code = fields.Char(string='Postal Code')
    state = fields.Char(string='State')

    # mindbody_client_credit_card.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_credit_card(self, data):
        """
        Prepare client credit card values from API response.
        
        Args:
            data (dict): Credit card data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.credit.card create/write
        """
        self.ensure_one()

        credit_card_vals = {
            'address': data.get('Address'),
            'card_holder': data.get('CardHolder'),
            'card_number': data.get('CardNumber'),
            'card_type': data.get('CardType'),
            'city': data.get('City'),
            'exp_month': data.get('ExpMonth'),
            'exp_year': data.get('ExpYear'),
            'last_four': data.get('LastFour'),
            'postal_code': data.get('PostalCode'),
            'state': data.get('State'),
        }

        # Remove None values
        credit_card_vals = {k: v for k, v in credit_card_vals.items() if v is not None and v is not False}

        return credit_card_vals

    # mindbody_client_credit_card.py

    def synchronize(self, from_date=None, to_date=None, limit=None, credit_card_ids=None):
        """
        Synchronize client credit cards from Mindbody to Odoo.
        Note: Client credit cards are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            credit_card_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Client credit cards are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
