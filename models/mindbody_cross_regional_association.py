import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyCrossRegionalAssociation(models.Model):
    _name = 'mindbody.cross.regional.association'
    _description = 'Mindbody Cross Regional Association'

    client_id = fields.Many2one('mindbody.client', string='Client')

    site_id = fields.Integer(string='Site ID')
    client_id_str = fields.Char(string='Client ID String')
    unique_id = fields.Integer(string='Unique ID')
    site_is_active = fields.Boolean(string='Site Is Active')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # Prepare Methods
    # ============================================

    @api.model
    def _prepare_cross_regional_association(self, data):
        """
        Prepare cross regional association values from API response.

        Args:
            data (dict): Cross regional association data from Mindbody API (from /client/crossregionalclientassociations endpoint)

        Returns:
            dict: Values ready for mindbody.cross.regional.association create/write
        """
        # Link to client if ClientId exists
        client_record_id = False
        if data.get('ClientId'):
            client = self.env['mindbody.client'].search(
                [('client_id', '=', data['ClientId'])], limit=1
            )
            if client:
                client_record_id = client.id

        association_vals = {
            'site_id': data.get('SiteId'),
            'client_id_str': data.get('ClientId'),
            'unique_id': data.get('UniqueId', 0),
            'site_is_active': data.get('SiteIsActive', False),
        }

        if client_record_id:
            association_vals['client_id'] = client_record_id

        # Remove None values
        association_vals = {k: v for k, v in association_vals.items() if v is not None}

        return association_vals

    # ============================================
    # Dummy Data Method
    # ============================================

    @api.model
    def _get_dummy_cross_regional_associations(self):
        """
        Return dummy cross regional associations data for testing when API returns no data.
        """
        # TODO: Replace with real API data when API key is available
        # TODO: API requires authentication - currently returns 401 Missing API key
        # TODO: This dummy data is for testing purposes only
        return {
            "PaginationResponse": {
                "RequestedLimit": 100,
                "RequestedOffset": 0,
                "PageSize": 10,
                "TotalResults": 10
            },
            "CrossRegionalClientAssociations": [
                {
                    "SiteId": 12345,
                    "ClientId": "100000001",
                    "UniqueId": 2001,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12346,
                    "ClientId": "100000001",
                    "UniqueId": 2002,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12347,
                    "ClientId": "100000002",
                    "UniqueId": 2003,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12345,
                    "ClientId": "100000003",
                    "UniqueId": 2004,
                    "SiteIsActive": False
                },
                {
                    "SiteId": 12348,
                    "ClientId": "100000004",
                    "UniqueId": 2005,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12349,
                    "ClientId": "100000005",
                    "UniqueId": 2006,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12345,
                    "ClientId": "100000006",
                    "UniqueId": 2007,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12350,
                    "ClientId": "100000007",
                    "UniqueId": 2008,
                    "SiteIsActive": False
                },
                {
                    "SiteId": 12346,
                    "ClientId": "100000008",
                    "UniqueId": 2009,
                    "SiteIsActive": True
                },
                {
                    "SiteId": 12351,
                    "ClientId": "100000009",
                    "UniqueId": 2010,
                    "SiteIsActive": True
                }
            ]
        }

    # ============================================
    # Synchronize Method
    # ============================================

    @api.model
    def synchronize(self, from_date=None, to_date=None, limit=None, association_ids=None):
        """
        Synchronize cross regional associations from Mindbody to Odoo.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            association_ids (list, optional): Specific association IDs to sync

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting cross regional association sync")

            associations_data = []
            response = {}

            # TODO: API requires authentication - currently returns 401 Missing API key
            # TODO: Uncomment below code when API key is configured
            # Prepare parameters
            params = {}
            if limit:
                params['Limit'] = limit
            if association_ids:
                params['AssociationIDs'] = ','.join(map(str, association_ids)) if isinstance(association_ids,
                                                                                             list) else association_ids

            try:
                response = api.get_client_crossregionalclientassociations(params=params)
                associations_data = response.get('CrossRegionalClientAssociations', []) if isinstance(response,
                                                                                                      dict) else []
            except Exception as api_error:
                _logger.warning(f"API call failed: {str(api_error)}")

            # TODO: Remove dummy data when real API is available with proper authentication
            # If no data from API, use dummy data for testing
            if not associations_data:
                _logger.info("No data from API, using dummy data for testing")
                response = self._get_dummy_cross_regional_associations()
                associations_data = response.get('CrossRegionalClientAssociations', [])

            if not associations_data:
                _logger.info("No cross regional associations found to sync")
                return stats

            _logger.info(f"Processing {len(associations_data)} cross regional associations")

            # Process each association
            for association_data in associations_data:
                try:
                    site_id = association_data.get('SiteId')
                    client_id_str = association_data.get('ClientId')

                    if not site_id or not client_id_str:
                        stats['skipped'] += 1
                        _logger.warning("Skipping association without SiteId or ClientId")
                        continue

                    # Check if association already exists
                    existing = self.search([
                        ('site_id', '=', site_id),
                        ('client_id_str', '=', client_id_str)
                    ], limit=1)

                    # Prepare association values
                    association_vals = self._prepare_cross_regional_association(association_data)

                    if existing:
                        existing.write(association_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated cross regional association for site {site_id}, client {client_id_str}")
                    else:
                        self.create(association_vals)
                        stats['created'] += 1
                        _logger.info(f"Created cross regional association for site {site_id}, client {client_id_str}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing cross regional association: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                pagination = self.env['mindbody.pagination.response']
                print(pagination._prepare_pagination_response(response['PaginationResponse']))

            _logger.info(
                f"Cross regional association sync completed: {stats['created']} created, {stats['updated']} updated, "
                f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync cross regional associations")
            stats['errors'] += 1
            raise UserError(f"Cross regional association sync failed: {str(e)}")

        return stats
