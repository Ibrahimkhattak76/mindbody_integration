import logging

_logger = logging.getLogger(__name__)
# mindbody_resource_availability.py
from odoo import models, fields


class MindbodyResourceAvailability(models.Model):
    _name = 'mindbody.resource.availability'
    _description = 'Mindbody Resource Availability'

    resource_id = fields.Integer(string='Resource ID')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    session_type_ids = fields.Char(string='Session Type IDs')  # JSON list
    program_ids = fields.Char(string='Program IDs')  # JSON list
    bookable_item_id = fields.Many2one('mindbody.bookable.item', string='Bookable Item')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    staff_availability_id = fields.Many2one('mindbody.staff.availability', string='Staff Availability')

    # mindbody_resource_availability.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_resource_availability(self, data):
        """
        Prepare resource availability values from API response.
        
        Args:
            data (dict): Resource availability data from Mindbody API (from /site/resourceavailabilities endpoint)
            
        Returns:
            dict: Values ready for mindbody.resource.availability create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        availability_vals = {
            'resource_id': data.get('ResourceId'),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'session_type_ids': str(data.get('SessionTypeIds', [])),
            'program_ids': str(data.get('ProgramIds', [])),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            availability_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        availability_vals = {k: v for k, v in availability_vals.items() if v is not None and v is not False}

        return availability_vals

    # mindbody_resource_availability.py

    def synchronize(self, from_date=None, to_date=None, limit=None, resource_availability_ids=None):
        """
        Synchronize resource availabilities from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for availabilities
            to_date (str, optional): End date for availabilities
            limit (int, optional): Maximum number of records to fetch
            resource_availability_ids (list, optional): Specific availability IDs to sync
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            # Prepare parameters
            params = {}
            if limit:
                params['Limit'] = limit
            if resource_availability_ids:
                params['ResourceAvailabilityIDs'] = ','.join(map(str, resource_availability_ids)) if isinstance(
                    resource_availability_ids, list) else resource_availability_ids
            if from_date:
                params['StartDateTime'] = from_date
                if to_date:
                    params['EndDateTime'] = to_date

            _logger.info(f"Starting resource availability sync with params: {params}")

            # Fetch resource availabilities from Mindbody API
            response = api.get_site_resourceavailabilities(params=params)
            availabilities_data = response.get('ResourceAvailabilities', []) if isinstance(response, dict) else []

            if not availabilities_data:
                _logger.info("No resource availabilities found to sync")
                return stats

            _logger.info(f"Fetched {len(availabilities_data)} resource availabilities from Mindbody")

            # Process each availability
            for availability_data in availabilities_data:
                try:
                    # Prepare availability values
                    availability_vals = self._prepare_resource_availability(availability_data)

                    # Check if availability already exists
                    existing = self.search([
                        ('resource_id', '=', availability_vals.get('resource_id')),
                        ('start_date_time', '=', availability_vals.get('start_date_time')),
                        ('end_date_time', '=', availability_vals.get('end_date_time'))
                    ], limit=1)

                    if existing:
                        existing.write(availability_vals)
                        stats['updated'] += 1
                        _logger.info(
                            f"Updated resource availability for resource {availability_vals.get('resource_id')}")
                    else:
                        self.create(availability_vals)
                        stats['created'] += 1
                        _logger.info(
                            f"Created resource availability for resource {availability_vals.get('resource_id')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing resource availability: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(
                f"Resource availability sync completed: {stats['created']} created, {stats['updated']} updated, "
                f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync resource availabilities")
            stats['errors'] += 1
            raise UserError(f"Resource availability sync failed: {str(e)}")

        return stats
