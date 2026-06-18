import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyScheduleItem(models.Model):
    _name = 'mindbody.schedule.item'
    _description = 'Mindbody Schedule Item'

    staff_member_ids = fields.One2many('mindbody.staff', 'schedule_item_id', string='Staff Members')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    def _prepare_schedule_item(self, data):
        """Prepare schedule item values - sync staff separately first"""

        # Collect staff IDs that need to be synced
        staff_ids_to_link = []

        for staff_data in data.get('StaffMembers', []):
            staff_id = staff_data.get('Id')
            if not staff_id:
                continue

            # Check if staff exists
            existing_staff = self.env['mindbody.staff'].search([('staff_id', '=', staff_id)], limit=1)

            if not existing_staff:
                # Staff doesn't exist - sync it first
                _logger.info(f"Staff {staff_id} not found, syncing...")
                try:
                    self.env['mindbody.staff'].synchronize(staff_ids=[staff_id])
                    existing_staff = self.env['mindbody.staff'].search([('staff_id', '=', staff_id)], limit=1)
                except Exception as e:
                    _logger.warning(f"Could not sync staff {staff_id}: {e}")
                    continue

            if existing_staff:
                staff_ids_to_link.append(existing_staff.id)

        schedule_item_vals = {}
        if staff_ids_to_link:
            # Use (6, 0, ids) to replace all relations
            schedule_item_vals['staff_member_ids'] = [(6, 0, staff_ids_to_link)]

        return schedule_item_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, schedule_item_ids=None):
        """Synchronize schedule items from Mindbody to Odoo"""
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if schedule_item_ids:
                params['ScheduleItemIDs'] = ','.join(map(str, schedule_item_ids)) if isinstance(schedule_item_ids,
                                                                                                list) else schedule_item_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            _logger.info(f"Starting schedule item sync with params: {params}")
            response = api.get_appointment_scheduleitems(params=params)
            schedule_items_data = response.get('StaffMembers', []) if isinstance(response, dict) else []

            if not schedule_items_data:
                _logger.info("No schedule items found to sync")
                return stats

            _logger.info(f"Fetched {len(schedule_items_data)} schedule items from Mindbody")

            for schedule_item_data in schedule_items_data:
                try:
                    schedule_item_vals = self._prepare_schedule_item({'StaffMembers': [schedule_item_data]})

                    if not schedule_item_vals:
                        stats['skipped'] += 1
                        continue

                    # Schedule items don't have unique IDs
                    existing = self.search([], limit=1)

                    if existing:
                        existing.write(schedule_item_vals)
                        stats['updated'] += 1
                        _logger.info("Updated schedule item")
                    else:
                        self.create(schedule_item_vals)
                        stats['created'] += 1
                        _logger.info("Created schedule item")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing schedule item: {str(e)}", exc_info=True)

            _logger.info(f"Schedule item sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync schedule items")
            raise UserError(f"Schedule item sync failed: {str(e)}")

        return stats

# import logging
#
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
# # mindbody_schedule_item.py
# from odoo import models, fields
#
#
# class MindbodyScheduleItem(models.Model):
#     _name = 'mindbody.schedule.item'
#     _description = 'Mindbody Schedule Item'
#
#     staff_member_ids = fields.One2many('mindbody.staff', 'schedule_item_id', string='Staff Members')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # mindbody_schedule_item.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_schedule_item(self, data):
#         """
#         Prepare schedule item values from API response.
#
#         Args:
#             data (dict): Schedule item data from Mindbody API (from /appointment/scheduleitems endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.schedule.item create/write
#         """
#         self.ensure_one()
#
#         # Prepare staff members (One2many)
#         staff_commands = []
#         for staff_data in data.get('StaffMembers', []):
#             staff_vals = self.env['mindbody.staff']._prepare_staff(staff_data)
#             if staff_vals:
#                 staff_commands.append((0, 0, staff_vals))
#
#         # Prepare pagination (Many2one)
#         pagination_vals = None
#         if data.get('PaginationResponse'):
#             pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
#                 data['PaginationResponse']
#             )
#
#         schedule_item_vals = {
#             # One2many fields
#             'staff_member_ids': staff_commands if staff_commands else None,
#         }
#
#         # Add Many2one fields with create commands
#         if pagination_vals:
#             schedule_item_vals['pagination_response_id'] = (0, 0, pagination_vals)
#
#         # Remove None values
#         schedule_item_vals = {k: v for k, v in schedule_item_vals.items() if v is not None and v is not False}
#
#         return schedule_item_vals
#
#     # mindbody_schedule_item.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, schedule_item_ids=None):
#         """
#         Synchronize schedule items from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for schedule items
#             to_date (str, optional): End date for schedule items
#             limit (int, optional): Maximum number of records to fetch
#             schedule_item_ids (list, optional): Specific schedule item IDs to sync
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
#             if limit:
#                 params['Limit'] = limit
#             if schedule_item_ids:
#                 params['ScheduleItemIDs'] = ','.join(map(str, schedule_item_ids)) if isinstance(schedule_item_ids,
#                                                                                                 list) else schedule_item_ids
#             if from_date:
#                 params['StartDate'] = from_date
#                 if to_date:
#                     params['EndDate'] = to_date
#
#             _logger.info(f"Starting schedule item sync with params: {params}")
#
#             # Fetch schedule items from Mindbody API
#             response = api.get_appointment_scheduleitems(params=params)
#             schedule_items_data = response.get('StaffMembers', []) if isinstance(response, dict) else []
#
#             if not schedule_items_data:
#                 _logger.info("No schedule items found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(schedule_items_data)} schedule items from Mindbody")
#
#             # Process each schedule item
#             for schedule_item_data in schedule_items_data:
#                 try:
#                     # Prepare schedule item values
#                     schedule_item_vals = self._prepare_schedule_item({'StaffMembers': [schedule_item_data]})
#
#                     # Check if schedule item already exists
#                     # This is a simplified approach - you may need to adjust based on your needs
#
#                     existing = self.search([], limit=1)
#                     if existing:
#                         existing.write(schedule_item_vals)
#                         stats['updated'] += 1
#                         _logger.info("Updated schedule item")
#                     else:
#                         self.create(schedule_item_vals)
#                         stats['created'] += 1
#                         _logger.info("Created schedule item")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing schedule item: {str(e)}", exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 self.env['mindbody.pagination.response'].create(
#                     self.env['mindbody.pagination.response']._prepare_pagination_response(
#                         response['PaginationResponse'])
#                 )
#
#             _logger.info(f"Schedule item sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync schedule items")
#             stats['errors'] += 1
#             raise UserError(f"Schedule item sync failed: {str(e)}")
#
#         return stats
