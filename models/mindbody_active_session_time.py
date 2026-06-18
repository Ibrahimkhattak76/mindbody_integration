import logging

_logger = logging.getLogger(__name__)
# mindbody_active_session_time.py
from odoo import models, fields


class MindbodyActiveSessionTime(models.Model):
    _name = 'mindbody.active.session.time'
    _description = 'Mindbody Active Session Time'

    time = fields.Char(string='Time')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_active_session_time(self, data):
        """
        Prepare active session time values from API response.
        
        Args:
            data (str/dict): Active session time string or dictionary
            
        Returns:
            dict: Values ready for mindbody.active.session.time create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if isinstance(data, dict) and data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        if isinstance(data, str):
            time_vals = {
                'time': data,
            }
        else:
            time_vals = {
                'time': data.get('time') or data.get('Time') or data.get('ActiveSessionTime'),
            }

        # Add Many2one fields with create commands
        if pagination_vals:
            time_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        time_vals = {k: v for k, v in time_vals.items() if v is not None and v is not False}

        return time_vals

    # mindbody_active_session_time.py

    def synchronize(self, from_date=None, to_date=None, limit=None, session_time_ids=None):
        """
        Synchronize active session times from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            session_time_ids (list, optional): Not used for this endpoint
            
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

            _logger.info(f"Starting active session time sync with params: {params}")

            # Fetch active session times from Mindbody API
            response = api.get_appointment_activesessiontimes(params=params)
            session_times_data = response.get('ActiveSessionTimes', []) if isinstance(response, dict) else []

            if not session_times_data:
                _logger.info("No active session times found to sync")
                return stats

            _logger.info(f"Fetched {len(session_times_data)} active session times from Mindbody")

            # Clear existing records and create new ones
            self.search([]).unlink()

            # Process each session time
            for session_time_data in session_times_data:
                try:
                    # Prepare session time values
                    session_time_vals = self._prepare_active_session_time(session_time_data)

                    self.create(session_time_vals)
                    stats['created'] += 1
                    _logger.info(f"Created active session time: {session_time_data}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing active session time: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Active session time sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync active session times")
            stats['errors'] += 1
            raise UserError(f"Active session time sync failed: {str(e)}")

        return stats
