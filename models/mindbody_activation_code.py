import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# mindbody_activation_code.py
from odoo import models, fields


class MindbodyActivationCode(models.Model):
    _name = 'mindbody.activation.code'
    _description = 'Mindbody Activation Code'

    site_id = fields.Many2one('mindbody.site', string='Site')

    activation_code = fields.Char(string='Activation Code')
    activation_link = fields.Char(string='Activation Link')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_activation_code(self, data):
        """
        Prepare activation code values from API response.
        
        Args:
            data (dict): Activation code data from Mindbody API (from /site/activationcode endpoint)
            
        Returns:
            dict: Values ready for mindbody.activation.code create/write
        """
        self.ensure_one()

        activation_vals = {
            'activation_code': data.get('ActivationCode'),
            'activation_link': data.get('ActivationLink'),
        }

        # Remove None values
        activation_vals = {k: v for k, v in activation_vals.items() if v is not None and v is not False}

        return activation_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, site_id=None):
        """
        Synchronize activation code from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used
            to_date (str, optional): Not used
            limit (int, optional): Not used
            site_id (int, optional): Site ID to get activation code for
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            # Prepare parameters
            params = {}
            if site_id:
                params['siteId'] = site_id

            # Fetch activation code from Mindbody API
            response = api.get_site_activationcode(params=params)

            if not response:
                return stats

            # Check if activation code already exists
            existing = self.search([], limit=1)

            # Prepare activation code values
            activation_vals = self._prepare_activation_code(response)

            if existing:
                existing.write(activation_vals)
                stats['updated'] += 1
                _logger.info("Updated activation code")
            else:
                self.create(activation_vals)
                stats['created'] += 1
                _logger.info("Created activation code")

            _logger.info(f"Activation code sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync activation code")
            stats['errors'] += 1
            raise UserError(f"Activation code sync failed: {str(e)}")

        return stats
