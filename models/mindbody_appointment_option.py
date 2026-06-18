import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyAppointmentOption(models.Model):
    _name = 'mindbody.appointment.option'
    _description = 'Mindbody Appointment Option'

    display_name = fields.Char(string='Display Name')
    name = fields.Char(string='Name')
    value = fields.Char(string='Value')
    option_type = fields.Char(string='Type')

    def _prepare_appointment_option(self, data):
        """Prepare appointment option values from API response"""
        option_vals = {
            'display_name': data.get('DisplayName'),
            'name': data.get('Name'),
            'value': data.get('Value'),
            'option_type': data.get('Type'),
        }
        return {k: v for k, v in option_vals.items() if v is not None and v is not False}

    def synchronize(self, from_date=None, to_date=None, limit=None, option_ids=None):
        """Synchronize appointment options from Mindbody to Odoo"""
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting appointment option sync")
            response = api.get_appointment_appointmentoptions()
            options_data = response.get('Options', []) if isinstance(response, dict) else []

            if not options_data:
                _logger.info("No appointment options found to sync")
                return stats

            _logger.info(f"Fetched {len(options_data)} appointment options from Mindbody")

            # Clear existing records and create new ones
            self.search([]).unlink()

            for option_data in options_data:
                try:
                    option_vals = self._prepare_appointment_option(option_data)
                    self.create(option_vals)
                    stats['created'] += 1
                    _logger.info(f"Created appointment option: {option_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing appointment option: {str(e)}", exc_info=True)

            _logger.info(f"Appointment option sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync appointment options")
            stats['errors'] += 1
            raise UserError(f"Appointment option sync failed: {str(e)}")

        return stats

# import logging
#
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
# # mindbody_appointment_option.py
# from odoo import models, fields
#
#
# class MindbodyAppointmentOption(models.Model):
#     _name = 'mindbody.appointment.option'
#     _description = 'Mindbody Appointment Option'
#
#     display_name = fields.Char(string='Display Name')
#     name = fields.Char(string='Name')
#     value = fields.Char(string='Value')
#     option_type = fields.Char(string='Type')
#
#     # mindbody_appointment_option.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_appointment_option(self, data):
#         """
#         Prepare appointment option values from API response.
#
#         Args:
#             data (dict): Appointment option data from Mindbody API (from /appointment/appointmentoptions endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.appointment.option create/write
#         """
#         self.ensure_one()
#
#         option_vals = {
#             'display_name': data.get('DisplayName'),
#             'name': data.get('Name'),
#             'value': data.get('Value'),
#             'option_type': data.get('Type'),
#         }
#
#         # Remove None values
#         option_vals = {k: v for k, v in option_vals.items() if v is not None and v is not False}
#
#         return option_vals
#
#     # mindbody_appointment_option.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, option_ids=None):
#         """
#         Synchronize appointment options from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Maximum number of records to fetch
#             option_ids (list, optional): Not used for this endpoint
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             _logger.info("Starting appointment option sync")
#
#             # Fetch appointment options from Mindbody API
#             response = api.get_appointment_appointmentoptions()
#             options_data = response.get('Options', []) if isinstance(response, dict) else []
#
#             if not options_data:
#                 _logger.info("No appointment options found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(options_data)} appointment options from Mindbody")
#
#             # Clear existing records and create new ones
#             self.search([]).unlink()
#
#             # Process each appointment option
#             for option_data in options_data:
#                 try:
#                     # Prepare appointment option values
#                     option_vals = self._prepare_appointment_option(option_data)
#
#                     self.create(option_vals)
#                     stats['created'] += 1
#                     _logger.info(f"Created appointment option: {option_data.get('Name')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing appointment option: {str(e)}", exc_info=True)
#                     continue
#
#             _logger.info(f"Appointment option sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync appointment options")
#             stats['errors'] += 1
#             raise UserError(f"Appointment option sync failed: {str(e)}")
#
#         return stats
