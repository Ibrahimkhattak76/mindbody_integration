# mindbody_pickaspot_spots.py
from odoo import models, fields


class MindbodyPickaspotSpots(models.Model):
    _name = 'mindbody.pickaspot.spots'
    _description = 'Mindbody Pick-a-Spot Spots'

    reserved_spot_numbers = fields.Char(string='Reserved Spot Numbers')  # JSON list
    available_spot_numbers = fields.Char(string='Available Spot Numbers')  # JSON list
    unavailable_spot_numbers = fields.Char(string='Unavailable Spot Numbers')  # JSON list

    # mindbody_pickaspot_spots.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_pickaspot_spots(self, data):
        """
        Prepare pick-a-spot spots values from API response.
        
        Args:
            data (dict): Pick-a-spot spots data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.pickaspot.spots create/write
        """
        self.ensure_one()

        spots_vals = {
            'reserved_spot_numbers': str(data.get('ReservedSpotNumbers', [])),
            'available_spot_numbers': str(data.get('AvailableSpotNumbers', [])),
            'unavailable_spot_numbers': str(data.get('UnavailableSpotNumbers', [])),
        }

        # Remove None values
        spots_vals = {k: v for k, v in spots_vals.items() if v is not None and v is not False}

        return spots_vals
