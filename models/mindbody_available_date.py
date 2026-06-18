import logging
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyAvailableDate(models.Model):
    _name = 'mindbody.available.date'
    _description = 'Mindbody Available Date'

    date = fields.Datetime(string='Date')
    session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')

    # ============================================
    # Helper Methods
    # ============================================

    def _parse_datetime(self, value):
        """Convert ISO 8601 datetime to Odoo format"""
        if not value:
            return False
        try:
            if isinstance(value, str):
                if 'Z' in value:
                    dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
                elif 'T' in value:
                    dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                else:
                    return value
                return fields.Datetime.to_string(dt)
            return value
        except Exception as e:
            _logger.warning(f"Failed to parse datetime '{value}': {str(e)}")
            return False

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_available_date(self, date_str, session_type_id=None):
        """Prepare available date record"""
        return {
            'date': self._parse_datetime(date_str),
            'session_type_id': session_type_id,
        }

    # ============================================
    # Wizard & Sync
    # ============================================

    def _open_session_type_wizard(self):
        """Open wizard to select Session Type before syncing"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Session Type',
            'res_model': 'session.type.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'mindbody.available.date',
                'default_limit': 100,
            }
        }

    def synchronize(self, from_date=None, to_date=None, limit=None, session_type_ids=None):
        """
        Synchronize Available Dates - Requires SessionTypeId
        """
        if not session_type_ids:
            return self._open_session_type_wizard()

        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {
                'SessionTypeIds': session_type_ids if isinstance(session_type_ids, list) else [session_type_ids]
            }
            if from_date:
                params['StartDate'] = from_date
            if to_date:
                params['EndDate'] = to_date
            if limit:
                params['Limit'] = limit

            _logger.info(f"Starting available date sync with params: {params}")

            response = api.get_appointment_availabledates(params=params)
            dates_data = response.get('AvailableDates', []) if isinstance(response, dict) else []

            if not dates_data:
                _logger.info("No available dates found")
                return stats

            _logger.info(f"Fetched {len(dates_data)} available dates")

            # Clear old records for selected session type
            self.search([('session_type_id', 'in', params['SessionTypeIds'])]).unlink()

            for date_str in dates_data:
                try:
                    date_vals = self._prepare_available_date(date_str, session_type_ids)
                    if date_vals.get('date'):
                        self.create(date_vals)
                        stats['created'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing date {date_str}: {e}")

            _logger.info(f"Available date sync completed: {stats}")

        except Exception as e:
            _logger.exception("Available date sync failed")
            raise UserError(f"Available date sync failed: {str(e)}")

        return stats

# import logging
#
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
# # mindbody_available_date.py
# from odoo import models, fields
#
#
# class MindbodyAvailableDate(models.Model):
#     _name = 'mindbody.available.date'
#     _description = 'Mindbody Available Date'
#
#     date = fields.Datetime(string='Date')
#
#     # mindbody_available_date.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_available_date(self, data):
#         """
#         Prepare available date values from API response.
#
#         Args:
#             data (str/dict): Available date string or dictionary
#
#         Returns:
#             dict: Values ready for mindbody.available.date create/write
#         """
#         self.ensure_one()
#
#         if isinstance(data, str):
#             date_vals = {
#                 'date': data,
#             }
#         else:
#             date_vals = {
#                 'date': data.get('date') or data.get('Date') or data.get('AvailableDate'),
#             }
#
#         # Remove None values
#         date_vals = {k: v for k, v in date_vals.items() if v is not None and v is not False}
#
#         return date_vals
#
#     # mindbody_available_date.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, date_ids=None):
#         """
#         Synchronize available dates from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for available dates
#             to_date (str, optional): End date for available dates
#             limit (int, optional): Not used for this endpoint
#             date_ids (list, optional): Not used for this endpoint
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             # Prepare parameters
#             params = {}
#             if from_date:
#                 params['StartDate'] = from_date
#             if to_date:
#                 params['EndDate'] = to_date
#
#             _logger.info(f"Starting available date sync with params: {params}")
#
#             # Fetch available dates from Mindbody API
#             response = api.get_appointment_availabledates(params=params)
#             dates_data = response.get('AvailableDates', []) if isinstance(response, dict) else []
#
#             if not dates_data:
#                 _logger.info("No available dates found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(dates_data)} available dates from Mindbody")
#
#             # Clear existing records and create new ones
#             self.search([]).unlink()
#
#             # Process each date
#             for date_data in dates_data:
#                 try:
#                     # Prepare available date values
#                     date_vals = self._prepare_available_date(date_data)
#
#                     self.create(date_vals)
#                     stats['created'] += 1
#                     _logger.info(f"Created available date: {date_data}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing available date: {str(e)}", exc_info=True)
#                     continue
#
#             _logger.info(f"Available date sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync available dates")
#             stats['errors'] += 1
#             raise UserError(f"Available date sync failed: {str(e)}")
#
#         return stats
