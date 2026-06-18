import base64
import logging

import requests

from odoo.exceptions import UserError
from .utils import safe_list

_logger = logging.getLogger(__name__)

from odoo import models, fields, api


class MindbodyLocation(models.Model):
    _name = 'mindbody.location'
    _description = 'Mindbody Location'

    location_id = fields.Integer(string='Location ID')
    additional_image_urls = fields.Char(string='Additional Image URLs')  # JSON list
    address = fields.Char(string='Address')
    address2 = fields.Char(string='Address 2')
    amenity_ids = fields.One2many('mindbody.amenity', 'location_id', string='Amenities')
    business_description = fields.Text(string='Business Description')
    city = fields.Char(string='City')
    description = fields.Text(string='Description')
    has_classes = fields.Boolean(string='Has Classes')
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

    # Additional fields from other endpoints
    business_id = fields.Integer(string='Business ID')
    facility_square_feet = fields.Integer(string='Facility Square Feet')
    pro_spa_finder_site = fields.Boolean(string='Pro Spa Finder Site')
    can_book = fields.Boolean(string='Can Book')
    number_treatment_rooms = fields.Integer(string='Number Treatment Rooms')
    active = fields.Boolean(string='Active')
    inv_active = fields.Boolean(string='Inventory Active')
    ws_show = fields.Boolean(string='Web Show')
    email = fields.Char(string='Email')
    contact_name = fields.Char(string='Contact Name')
    ship_address = fields.Char(string='Ship Address')
    ship_state = fields.Char(string='Ship State')
    ship_postal = fields.Char(string='Ship Postal')
    ship_phone = fields.Char(string='Ship Phone')
    ship_poc = fields.Char(string='Ship POC')
    tax_grouping = fields.Boolean(string='Tax Grouping')
    label_tax1 = fields.Char(string='Label Tax 1')
    label_tax2 = fields.Char(string='Label Tax 2')
    label_tax3 = fields.Char(string='Label Tax 3')
    label_tax4 = fields.Char(string='Label Tax 4')
    label_tax5 = fields.Char(string='Label Tax 5')
    wac = fields.Boolean(string='WAC')
    ship_address2 = fields.Char(string='Ship Address 2')
    master_loc_id = fields.Integer(string='Master Location ID')
    street_address = fields.Char(string='Street Address')
    country = fields.Char(string='Country')
    ext = fields.Char(string='Extension')
    distance_in_miles = fields.Float(string='Distance In Miles')
    image_url = fields.Char(string='Image URL')
    has_site = fields.Boolean(string='Has Site')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    main_image = fields.Binary(string='Image', compute='_compute_main_image', store=True)

    @api.depends('image_url')
    def _compute_main_image(self):
        for record in self:
            record.main_image = False
            if record.image_url:
                try:
                    resp = requests.get(record.image_url, timeout=5)
                    if resp.status_code == 200:
                        record.main_image = base64.b64encode(resp.content)
                except Exception:
                    continue

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name if record.name else str(record.location_id)

    def _prepare_location(self, data):
        """
        Prepare location values from API response.
        
        Args:
            data (dict): Location data from Mindbody API (from /site/locations endpoint)
            
        Returns:
            dict: Values ready for mindbody.location create/write
        """

        # Prepare amenities (One2many)
        amenity_commands = []
        for amenity_data in safe_list(data.get('Amenities', [])):
            amenity_vals = self.env['mindbody.amenity']._prepare_amenity(amenity_data)
            if amenity_vals:
                amenity_commands.append((0, 0, amenity_vals))

        location_vals = {
            'location_id': data.get('Id'),
            'additional_image_urls': str(data.get('AdditionalImageURLs', [])),
            'address': data.get('Address'),
            'address2': data.get('Address2'),
            'business_description': data.get('BusinessDescription'),
            'city': data.get('City'),
            'description': data.get('Description'),
            'has_classes': data.get('HasClasses', False),
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

            # Additional fields
            'business_id': data.get('BusinessId'),
            'facility_square_feet': data.get('FacilitySquareFeet', 0),
            'pro_spa_finder_site': data.get('ProSpaFinderSite', False),
            'can_book': data.get('CanBook', False),
            'number_treatment_rooms': data.get('NumberTreatmentRooms', 0),
            'active': data.get('Active', True),
            'inv_active': data.get('InvActive', True),
            'ws_show': data.get('WsShow', True),
            'email': data.get('Email'),
            'contact_name': data.get('ContactName'),
            'ship_address': data.get('ShipAddress'),
            'ship_state': data.get('ShipState'),
            'ship_postal': data.get('ShipPostal'),
            'ship_phone': data.get('ShipPhone'),
            'ship_poc': data.get('ShipPOC'),
            'tax_grouping': data.get('TaxGrouping', False),
            'label_tax1': data.get('LabelTax1'),
            'label_tax2': data.get('LabelTax2'),
            'label_tax3': data.get('LabelTax3'),
            'label_tax4': data.get('LabelTax4'),
            'label_tax5': data.get('LabelTax5'),
            'wac': data.get('WAC', False),
            'ship_address2': data.get('ShipAddress2'),
            'master_loc_id': data.get('MasterLocId'),
            'street_address': data.get('StreetAddress'),
            'country': data.get('Country'),
            'ext': data.get('Ext'),
            'distance_in_miles': data.get('DistanceInMiles', 0.0),
            'image_url': data.get('ImageURL'),
            'has_site': data.get('HasSite', False),
            # One2many fields
            'amenity_ids': amenity_commands if amenity_commands else None,
        }

        # Remove None values
        location_vals = {k: v for k, v in location_vals.items() if v is not None and v is not False}

        return location_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, location_ids=None):
        """
        Synchronize locations from Mindbody to Odoo with pagination.
        REAL API data only.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        offset = 0
        page_size = limit if limit else 100
        has_more = True

        try:
            while has_more:
                params = {
                    'Limit': page_size,
                    'Offset': offset,
                }
                if location_ids:
                    params['LocationIDs'] = ','.join(map(str, location_ids)) if isinstance(location_ids,
                                                                                           list) else location_ids
                if from_date:
                    params['ModifiedDateTime'] = from_date
                    if to_date:
                        params['ModifiedDateTime'] = f"{from_date},{to_date}"

                _logger.info(f"Fetching locations, offset={offset}, limit={page_size}")

                response = api.get_site_locations(params=params)
                locations_data = response.get('Locations', []) if isinstance(response, dict) else []

                if not locations_data:
                    break

                _logger.info(f"Fetched {len(locations_data)} locations from Mindbody")

                for location_data in locations_data:
                    try:
                        location_id = location_data.get('Id')
                        if not location_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping location without ID")
                            continue

                        existing = self.search([('location_id', '=', location_id)], limit=1)
                        location_vals = self._prepare_location(location_data)

                        if existing:
                            existing.write(location_vals)
                            stats['updated'] += 1
                        else:
                            self.create(location_vals)
                            stats['created'] += 1

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing location {location_data.get('Id')}: {str(e)}", exc_info=True)
                        continue

                # Pagination check
                if len(locations_data) < page_size:
                    has_more = False

                    if isinstance(response, dict) and response.get('PaginationResponse'):
                        pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                            response['PaginationResponse']
                        )
                        if pagination_vals:
                            self.env['mindbody.pagination.response'].create(pagination_vals)
                else:
                    offset += page_size

            _logger.info(f"Location sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync locations")
            stats['errors'] += 1
            raise UserError(f"Location sync failed: {str(e)}")

        return stats
    # def synchronize(self, from_date=None, to_date=None, limit=None, location_ids=None):
    #     """
    #     Synchronize locations from Mindbody to Odoo.
    #
    #     Args:
    #         from_date (str, optional): Start date for modified locations
    #         to_date (str, optional): End date for modified locations
    #         limit (int, optional): Maximum number of records to fetch
    #         location_ids (list, optional): Specific location IDs to sync
    #
    #     Returns:
    #         dict: Statistics of created/updated records
    #     """
    #     api = self.env['mindbody.api']
    #     stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
    #
    #     try:
    #         # Prepare parameters
    #         params = {}
    #         if limit:
    #             params['Limit'] = limit
    #         if location_ids:
    #             params['LocationIDs'] = ','.join(map(str, location_ids)) if isinstance(location_ids,
    #                                                                                    list) else location_ids
    #         if from_date:
    #             params['ModifiedDateTime'] = from_date
    #             if to_date:
    #                 params['ModifiedDateTime'] = f"{from_date},{to_date}"
    #
    #         _logger.info(f"Starting location sync with params: {params}")
    #
    #         # Fetch locations from Mindbody API
    #         response = api.get_site_locations(params=params)
    #         locations_data = response.get('Locations', []) if isinstance(response, dict) else []
    #
    #         if not locations_data:
    #             _logger.info("No locations found to sync")
    #             return stats
    #
    #         _logger.info(f"Fetched {len(locations_data)} locations from Mindbody")
    #
    #         # Process each location
    #         for location_data in locations_data:
    #             try:
    #                 location_id = location_data.get('Id')
    #                 if not location_id:
    #                     stats['skipped'] += 1
    #                     _logger.warning("Skipping location without ID")
    #                     continue
    #
    #                 # Check if location already exists
    #                 existing = self.search([('location_id', '=', location_id)], limit=1)
    #
    #                 # Prepare location values
    #                 location_vals = self._prepare_location(location_data)
    #
    #                 if existing:
    #                     existing.write(location_vals)
    #                     stats['updated'] += 1
    #                     _logger.info(f"Updated location {location_id}: {location_data.get('Name')}")
    #                 else:
    #                     self.create(location_vals)
    #                     stats['created'] += 1
    #                     _logger.info(f"Created location {location_id}: {location_data.get('Name')}")
    #
    #             except Exception as e:
    #                 stats['errors'] += 1
    #                 _logger.error(f"Error processing location {location_data.get('Id')}: {str(e)}", exc_info=True)
    #                 continue
    #
    #         # Save pagination info if available
    #         if isinstance(response, dict) and response.get('PaginationResponse'):
    #             self.env['mindbody.pagination.response'].create(
    #                 self.env['mindbody.pagination.response']._prepare_pagination_response(
    #                     response['PaginationResponse'])
    #             )
    #
    #         _logger.info(f"Location sync completed: {stats['created']} created, {stats['updated']} updated, "
    #                      f"{stats['errors']} errors, {stats['skipped']} skipped")
    #
    #     except Exception as e:
    #         _logger.exception("Failed to sync locations")
    #         stats['errors'] += 1
    #         raise UserError(f"Location sync failed: {str(e)}")
    #
    #     return stats
