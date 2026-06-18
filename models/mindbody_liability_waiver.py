import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# mindbody_liability_waiver.py
from odoo import models, fields


class MindbodyLiabilityWaiver(models.Model):
    _name = 'mindbody.liability.waiver'
    _description = 'Mindbody Liability Waiver'

    site_id = fields.Many2one('mindbody.site', string='Site')

    liability_waiver = fields.Text(string='Liability Waiver')

    # mindbody_liability_waiver.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_liability_waiver(self, data):
        """
        Prepare liability waiver values from API response.
        
        Args:
            data (dict): Liability waiver data from Mindbody API (from /site/liabilitywaiver endpoint)
            
        Returns:
            dict: Values ready for mindbody.liability.waiver create/write
        """
        self.ensure_one()

        waiver_vals = {
            'liability_waiver': data.get('LiabilityWaiver'),
        }

        # Remove None values
        waiver_vals = {k: v for k, v in waiver_vals.items() if v is not None and v is not False}

        return waiver_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, site_id=None):
        """
        Synchronize liability waiver from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used
            to_date (str, optional): Not used
            limit (int, optional): Not used
            site_id (int, optional): Site ID to get liability waiver for
            
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

            # Fetch liability waiver from Mindbody API
            response = api.get_site_liabilitywaiver(params=params)

            if not response:
                return stats

            # Check if liability waiver already exists
            existing = self.search([], limit=1)

            # Prepare liability waiver values
            waiver_vals = self._prepare_liability_waiver(response)

            if existing:
                existing.write(waiver_vals)
                stats['updated'] += 1
                _logger.info("Updated liability waiver")
            else:
                self.create(waiver_vals)
                stats['created'] += 1
                _logger.info("Created liability waiver")

            _logger.info(f"Liability waiver sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync liability waiver")
            stats['errors'] += 1
            raise UserError(f"Liability waiver sync failed: {str(e)}")

        return stats
