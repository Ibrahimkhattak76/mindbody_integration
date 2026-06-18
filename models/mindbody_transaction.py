# mindbody_transaction.py
from odoo import models, fields


class MindbodyTransaction(models.Model):
    _name = 'mindbody.transaction'
    _description = 'Mindbody Transaction'

    transaction_id = fields.Integer(string='Transaction ID')
    sale_id = fields.Integer(string='Sale ID')
    client_id = fields.Integer(string='Client ID')
    amount = fields.Float(string='Amount')
    settled = fields.Boolean(string='Settled')
    status = fields.Char(string='Status')
    transaction_time = fields.Datetime(string='Transaction Time')
    auth_time = fields.Datetime(string='Auth Time')
    location_id = fields.Integer(string='Location ID')
    merchant_id = fields.Char(string='Merchant ID')
    terminal_id = fields.Char(string='Terminal ID')
    card_expiration_month = fields.Char(string='Card Expiration Month')
    card_expiration_year = fields.Char(string='Card Expiration Year')
    cc_last_four = fields.Char(string='CC Last Four')
    card_type = fields.Char(string='Card Type')
    cc_swiped = fields.Boolean(string='CC Swiped')
    ach_last_four = fields.Char(string='ACH Last Four')
    authentication_url = fields.Char(string='Authentication URL')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')

    # mindbody_transaction.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_transaction(self, data):
        """
        Prepare transaction values from API response.
        
        Args:
            data (dict): Transaction data from Mindbody API (from /sale/transactions endpoint)
            
        Returns:
            dict: Values ready for mindbody.transaction create/write
        """
        # self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        transaction_vals = {
            'transaction_id': data.get('TransactionId'),
            'sale_id': data.get('SaleId'),
            'client_id': data.get('ClientId'),
            'amount': data.get('Amount', 0.0),
            'settled': data.get('Settled', False),
            'status': data.get('Status'),
            'transaction_time': data.get('TransactionTime'),
            'auth_time': data.get('AuthTime'),
            'location_id': data.get('LocationId'),
            'merchant_id': data.get('MerchantId'),
            'terminal_id': data.get('TerminalId'),
            'card_expiration_month': data.get('CardExpirationMonth'),
            'card_expiration_year': data.get('CardExpirationYear'),
            'cc_last_four': data.get('CCLastFour'),
            'card_type': data.get('CardType'),
            'cc_swiped': data.get('CCSwiped', False),
            'ach_last_four': data.get('ACHLastFour'),
            'authentication_url': data.get('AuthenticationUrl'),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            transaction_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        transaction_vals = {k: v for k, v in transaction_vals.items() if v is not None and v is not False}

        return transaction_vals
