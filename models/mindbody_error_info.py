# mindbody_error_info.py
from odoo import models, fields


class MindbodyErrorInfo(models.Model):
    _name = 'mindbody.error.info'
    _description = 'Mindbody Error Information'

    error_type = fields.Char(string='Type')
    message = fields.Char(string='Message')
    code = fields.Char(string='Code')
    reason_code = fields.Char(string='Reason Code')
    authentication_redirect_url = fields.Char(string='Authentication Redirect URL')
    operation = fields.Char(string='Operation')

    # mindbody_error_info.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_error_info(self, data):
        """
        Prepare error info values from API response.
        
        Args:
            data (dict): Error info data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.error.info create/write
        """
        self.ensure_one()

        error_vals = {
            'error_type': data.get('Type') or data.get('error_type'),
            'message': data.get('Message') or data.get('message'),
            'code': data.get('Code') or data.get('code'),
            'reason_code': data.get('ReasonCode') or data.get('reason_code'),
            'authentication_redirect_url': data.get('AuthenticationRedirectUrl'),
            'operation': data.get('Operation'),
        }

        # Remove None values
        error_vals = {k: v for k, v in error_vals.items() if v is not None and v is not False}

        return error_vals
