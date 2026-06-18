import logging

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodyAmenity(models.Model):
    _name = 'mindbody.amenity'
    _description = 'Mindbody Amenity'

    amenity_id = fields.Integer(string='Amenity ID')
    name = fields.Char(string='Name')
    location_id = fields.Many2one('mindbody.location', string='Location')
    # todo to be removed if not needed
    home_location_id = fields.Many2one('mindbody.home.location', string='Home Location')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_amenity(self, data):
        """
        Prepare amenity values from API response.
        Args:
            data (dict): Amenity data from Mindbody API
        Returns:
            dict: Values ready for mindbody.amenity create/write
        """
        amenity_vals = {
            'amenity_id': data.get('Id'),
            'name': data.get('Name'),
        }
        return {k: v for k, v in amenity_vals.items() if v is not None and v is not False}

    def synchronize(self):
        """
        Synchronize amenities from Mindbody to Odoo.
        Note: Amenities are typically synced as part of location sync.

        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Amenities are synced automatically during location sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
