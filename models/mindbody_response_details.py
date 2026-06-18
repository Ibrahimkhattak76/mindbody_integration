# mindbody_response_details.py
from odoo import models, fields


class MindbodyResponseDetails(models.Model):
    _name = 'mindbody.response.details'
    _description = 'Mindbody Response Details'

    status = fields.Char(string='Status')
    transaction_id = fields.Char(string='Transaction ID')
    message = fields.Char(string='Message')

    # mindbody_response_details.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_response_details(self, data):
        """
        Prepare response details values from API response.
        
        Args:
            data (dict): Response details data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.response.details create/write
        """
        self.ensure_one()

        response_vals = {
            'status': data.get('Status'),
            'transaction_id': data.get('TransactionId'),
            'message': data.get('Message'),
        }

        # Remove None values
        response_vals = {k: v for k, v in response_vals.items() if v is not None and v is not False}

        return response_vals
