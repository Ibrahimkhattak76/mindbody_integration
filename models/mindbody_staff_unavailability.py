import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_unavailability.py
from odoo import models, fields


class MindbodyStaffUnavailability(models.Model):
    _name = 'mindbody.staff.unavailability'
    _description = 'Mindbody Staff Unavailability'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    unavailability_id = fields.Integer(string='Unavailability ID')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    description = fields.Text(string='Description')

    # mindbody_staff_unavailability.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_unavailability(self, data):
        """
        Prepare staff unavailability values from API response.
        
        Args:
            data (dict): Staff unavailability data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.staff.unavailability create/write
        """
        self.ensure_one()

        unavailability_vals = {
            'unavailability_id': data.get('Id'),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'description': data.get('Description'),
        }

        # Remove None values
        unavailability_vals = {k: v for k, v in unavailability_vals.items() if v is not None and v is not False}

        return unavailability_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_id=None):
        """
        Synchronize staff unavailabilities from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for unavailabilities
            to_date (str, optional): End date for unavailabilities
            limit (int, optional): Maximum number of records to fetch
            staff_id (int, optional): Specific staff ID to sync unavailabilities for
            
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
            if staff_id:
                params['StaffId'] = staff_id
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            # Fetch appointment unavailabilities from Mindbody API
            response = api.get_appointment_unavailabilities(params=params)
            unavailabilities_data = response.get('Unavailabilities', []) if isinstance(response, dict) else []

            if not unavailabilities_data:
                return stats

            # Process each unavailability
            for unavailability_data in unavailabilities_data:
                try:
                    unavailability_id = unavailability_data.get('Id')
                    if not unavailability_id:
                        stats['skipped'] += 1
                        continue

                    # Check if unavailability already exists
                    existing = self.search([('unavailability_id', '=', unavailability_id)], limit=1)

                    # Prepare unavailability values
                    unavailability_vals = self._prepare_staff_unavailability(unavailability_data)

                    if existing:
                        existing.write(unavailability_vals)
                        stats['updated'] += 1
                    else:
                        self.create(unavailability_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Staff unavailabilities sync failed: {str(e)}")

        return stats
