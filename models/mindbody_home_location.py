import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyHomeLocation(models.Model):
    _name = 'mindbody.home.location'
    _description = 'Mindbody Home Location'

    client_id = fields.Many2one('mindbody.client', string='Client')
    location_id = fields.Many2one('mindbody.location', string='Location')

    additional_image_urls = fields.Char(string='Additional Image URLs')  # JSON list
    address = fields.Char(string='Address')
    address2 = fields.Char(string='Address 2')
    amenity_ids = fields.One2many('mindbody.amenity', 'home_location_id', string='Amenities')
    business_description = fields.Text(string='Business Description')
    city = fields.Char(string='City')
    description = fields.Text(string='Description')
    has_classes = fields.Boolean(string='Has Classes')
    external_id = fields.Integer(string='Location ID')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    name = fields.Char(string='Name')
    phone = fields.Char(string='Phone')
    phone_extension = fields.Char(string='Phone Extension')
    postal_code = fields.Char(string='Postal Code')
    site_id = fields.Integer(string='Site ID')
    state_prov_code = fields.Char(string='State/Prov Code')
    tax1 = fields.Float(string='Tax 1')
    tax2 = fields.Float(string='Tax 2')
    tax3 = fields.Float(string='Tax 3')
    tax4 = fields.Float(string='Tax 4')
    tax5 = fields.Float(string='Tax 5')
    total_number_of_ratings = fields.Integer(string='Total Number of Ratings')
    average_rating = fields.Float(string='Average Rating')
    total_number_of_deals = fields.Integer(string='Total Number of Deals')

    # mindbody_home_location.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_home_location(self, data):
        """
        Prepare home location values from API response.
        
        Args:
            data (dict): Home location data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.home.location create/write
        """

        # Prepare amenities (One2many)
        amenity_commands = []
        for amenity_data in data.get('Amenities', []):
            amenity_vals = self.env['mindbody.amenity']._prepare_amenity(amenity_data)
            if amenity_vals:
                amenity_commands.append((0, 0, amenity_vals))

        home_location_vals = {
            'additional_image_urls': str(data.get('AdditionalImageURLs', [])),
            'address': data.get('Address'),
            'address2': data.get('Address2'),
            'business_description': data.get('BusinessDescription'),
            'city': data.get('City'),
            'description': data.get('Description'),
            'has_classes': data.get('HasClasses', False),
            'id': data.get('Id'),
            'latitude': data.get('Latitude', 0.0),
            'longitude': data.get('Longitude', 0.0),
            'name': data.get('Name'),
            'phone': data.get('Phone'),
            'phone_extension': data.get('PhoneExtension'),
            'postal_code': data.get('PostalCode'),
            'site_id': data.get('SiteID'),
            'state_prov_code': data.get('StateProvCode'),
            'tax1': data.get('Tax1', 0.0),
            'tax2': data.get('Tax2', 0.0),
            'tax3': data.get('Tax3', 0.0),
            'tax4': data.get('Tax4', 0.0),
            'tax5': data.get('Tax5', 0.0),
            'total_number_of_ratings': data.get('TotalNumberOfRatings', 0),
            'average_rating': data.get('AverageRating', 0.0),
            'total_number_of_deals': data.get('TotalNumberOfDeals', 0),

            # One2many fields
            'amenity_ids': amenity_commands if amenity_commands else None,
        }

        # Remove None values
        home_location_vals = {k: v for k, v in home_location_vals.items() if v is not None and v is not False}

        return home_location_vals

    # mindbody_home_location.py

    def synchronize(self, from_date=None, to_date=None, limit=None, home_location_ids=None):
        """
        Synchronize home locations from Mindbody to Odoo.
        Note: Home locations are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            home_location_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Home locations are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
