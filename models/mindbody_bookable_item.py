import logging
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyBookableItem(models.Model):
    _name = 'mindbody.bookable.item'
    _description = 'Mindbody Bookable Item'

    bookable_item_id = fields.Integer(string='Bookable Item ID')
    staff_id = fields.Many2one('mindbody.staff', string='Staff')
    session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')
    program_ids = fields.One2many('mindbody.program', 'bookable_item_id', string='Programs')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    bookable_end_date_time = fields.Datetime(string='Bookable End Date Time')
    location_id = fields.Many2one('mindbody.location', string='Location')
    prep_time = fields.Integer(string='Prep Time')
    finish_time = fields.Integer(string='Finish Time')
    is_masked = fields.Boolean(string='Is Masked')
    show_public = fields.Boolean(string='Show Public')
    resource_availability_ids = fields.One2many('mindbody.resource.availability', 'bookable_item_id',
                                                string='Resource Availabilities')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    def _parse_datetime(self, value):
        """Convert ISO 8601 datetime to Odoo format"""
        if not value:
            return False
        try:
            if 'Z' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            elif 'T' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            else:
                return value
            return fields.Datetime.to_string(dt)
        except Exception as e:
            _logger.warning(f"Failed to parse datetime '{value}': {str(e)}")
            return False

    def _get_or_sync_staff(self, staff_id_val):
        """Get or sync staff member"""
        if not staff_id_val:
            return False
        staff = self.env['mindbody.staff'].search([('staff_id', '=', staff_id_val)], limit=1)
        if staff:
            return staff
        _logger.info(f"Staff {staff_id_val} not found, syncing...")
        self.env['mindbody.staff'].synchronize(staff_ids=[staff_id_val])
        return self.env['mindbody.staff'].search([('staff_id', '=', staff_id_val)], limit=1)

    def _get_or_sync_location(self, location_id_val):
        """Get or sync location"""
        if not location_id_val:
            return False
        location = self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)
        if location:
            return location
        _logger.info(f"Location {location_id_val} not found, syncing...")
        self.env['mindbody.location'].synchronize(location_ids=[location_id_val])
        return self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)

    def _get_or_sync_session_type(self, session_type_id_val):
        """Get or sync session type"""
        if not session_type_id_val:
            return False
        session_type = self.env['mindbody.session.type'].search([('session_type_id', '=', session_type_id_val)],
                                                                limit=1)
        if session_type:
            return session_type
        _logger.info(f"Session type {session_type_id_val} not found, syncing...")
        self.env['mindbody.session.type'].synchronize(session_type_ids=[session_type_id_val])
        return self.env['mindbody.session.type'].search([('session_type_id', '=', session_type_id_val)], limit=1)

    def _prepare_bookable_item(self, data):
        """Prepare bookable item values from API response"""

        staff = self._get_or_sync_staff(data.get('Staff', {}).get('Id'))
        location = self._get_or_sync_location(data.get('Location', {}).get('Id'))
        session_type = self._get_or_sync_session_type(data.get('SessionType', {}).get('Id'))

        program_commands = []
        for prog_data in data.get('Programs', []):
            prog_vals = self.env['mindbody.program']._prepare_program(prog_data)
            if prog_vals:
                program_commands.append((0, 0, prog_vals))

        resource_avail_commands = []
        for res_avail_data in data.get('ResourceAvailabilities', []):
            res_avail_vals = self.env['mindbody.resource.availability']._prepare_resource_availability(res_avail_data)
            if res_avail_vals:
                resource_avail_commands.append((0, 0, res_avail_vals))

        bookable_item_vals = {
            'bookable_item_id': data.get('Id'),
            'start_date_time': self._parse_datetime(data.get('StartDateTime')),
            'end_date_time': self._parse_datetime(data.get('EndDateTime')),
            'bookable_end_date_time': self._parse_datetime(data.get('BookableEndDateTime')),
            'prep_time': data.get('PrepTime', 0),
            'finish_time': data.get('FinishTime', 0),
            'is_masked': data.get('IsMasked', False),
            'show_public': data.get('ShowPublic', False),
            'staff_id': staff.id if staff else False,
            'location_id': location.id if location else False,
            'session_type_id': session_type.id if session_type else False,
        }

        if program_commands:
            bookable_item_vals['program_ids'] = program_commands
        if resource_avail_commands:
            bookable_item_vals['resource_availability_ids'] = resource_avail_commands

        return {k: v for k, v in bookable_item_vals.items() if v is not None}

    def _open_selection_wizard(self, limit=None, bookable_item_ids=None):
        """Open wizard to select session types"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Session Types',
            'res_model': 'session.type.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_limit': limit,
                'default_bookable_item_ids': bookable_item_ids,
            }
        }

    def synchronize(self, session_type_ids=None, limit=None, bookable_item_ids=None):
        """Synchronize bookable items from Mindbody to Odoo"""
        if not session_type_ids:
            return self._open_selection_wizard(limit, bookable_item_ids)

        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if bookable_item_ids:
                params['BookableItemIDs'] = ','.join(map(str, bookable_item_ids)) if isinstance(bookable_item_ids,
                                                                                                list) else bookable_item_ids
            if session_type_ids:
                params['SessionTypeIds'] = session_type_ids if isinstance(session_type_ids,
                                                                          list) else session_type_ids.ids

            _logger.info(f"Starting bookable item sync with params: {params}")
            response = api.get_appointment_bookableitems(params=params)
            bookable_items_data = response.get('Availabilities', []) if isinstance(response, dict) else []

            if not bookable_items_data:
                _logger.info("No bookable items found to sync")
                return stats

            _logger.info(f"Fetched {len(bookable_items_data)} bookable items from Mindbody")

            for bookable_item_data in bookable_items_data:
                try:
                    bookable_item_id = bookable_item_data.get('Id')
                    if not bookable_item_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.search([('bookable_item_id', '=', bookable_item_id)], limit=1)
                    bookable_item_vals = self._prepare_bookable_item(bookable_item_data)

                    if existing:
                        if 'program_ids' in bookable_item_vals:
                            existing.program_ids.unlink()
                        if 'resource_availability_ids' in bookable_item_vals:
                            existing.resource_availability_ids.unlink()
                        existing.write(bookable_item_vals)
                        stats['updated'] += 1
                    else:
                        self.create(bookable_item_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing bookable item {bookable_item_data.get('Id')}: {str(e)}",
                                  exc_info=True)

            _logger.info(f"Bookable item sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync bookable items")
            raise UserError(f"Bookable item sync failed: {str(e)}")

        return stats

# import logging
#
# from odoo.exceptions import UserError
# from .utils import safe_list, safe_dates
#
# _logger = logging.getLogger(__name__)
#
# from odoo import models, fields
#
#
# class MindbodyBookableItem(models.Model):
#     _name = 'mindbody.bookable.item'
#     _description = 'Mindbody Bookable Item'
#
#     bookable_item_id = fields.Integer(string='Bookable Item ID')
#     staff_id = fields.Many2one('mindbody.staff', string='Staff')
#     session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')
#     program_ids = fields.One2many('mindbody.program', 'bookable_item_id', string='Programs')
#     start_date_time = fields.Datetime(string='Start Date Time')
#     end_date_time = fields.Datetime(string='End Date Time')
#     bookable_end_date_time = fields.Datetime(string='Bookable End Date Time')
#     location_id = fields.Many2one('mindbody.location', string='Location')
#     prep_time = fields.Integer(string='Prep Time')
#     finish_time = fields.Integer(string='Finish Time')
#     is_masked = fields.Boolean(string='Is Masked')
#     show_public = fields.Boolean(string='Show Public')
#     resource_availability_ids = fields.One2many('mindbody.resource.availability', 'bookable_item_id',
#                                                 string='Resource Availabilities')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # Prepare Methods
#     def _prepare_bookable_item(self, data):
#         """
#         Prepare bookable item values from API response.
#
#         Args:
#             data (dict): Bookable item data from Mindbody API (from /appointment/bookableitems endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.bookable.item create/write
#         """
#         # Prepare staff (Many2one)
#         staff_vals = None
#         if data.get('Staff'):
#             staff_vals = self.env['mindbody.staff']._prepare_staff(data['Staff'])
#
#         # Prepare session type (Many2one)
#         session_type_vals = None
#         if data.get('SessionType'):
#             session_type_vals = self.env['mindbody.session.type']._prepare_session_type(data['SessionType'])
#
#         # Prepare programs (One2many)
#         program_commands = []
#         for prog_data in safe_list(data.get('Programs', [])):
#             prog_vals = self.env['mindbody.program']._prepare_program(prog_data)
#             if prog_vals:
#                 program_commands.append((0, 0, prog_vals))
#
#         # Prepare location (Many2one)
#         location_vals = None
#         if data.get('Location'):
#             location_vals = self.env['mindbody.location']._prepare_location(data['Location'])
#
#         # Prepare resource availabilities (One2many)
#         resource_avail_commands = []
#         for res_avail_data in safe_list(data.get('ResourceAvailabilities', [])):
#             res_avail_vals = self.env['mindbody.resource.availability']._prepare_resource_availability(res_avail_data)
#             if res_avail_vals:
#                 resource_avail_commands.append((0, 0, res_avail_vals))
#
#         bookable_item_vals = {
#             'bookable_item_id': data.get('Id'),
#             'start_date_time': safe_dates(data.get('StartDateTime')),
#             'end_date_time': safe_dates(data.get('EndDateTime')),
#             'bookable_end_date_time': safe_dates(data.get('BookableEndDateTime')),
#             'prep_time': data.get('PrepTime', 0),
#             'finish_time': data.get('FinishTime', 0),
#             'is_masked': data.get('IsMasked', False),
#             'show_public': data.get('ShowPublic', False),
#
#             # One2many fields
#             'program_ids': program_commands if program_commands else None,
#             'resource_availability_ids': resource_avail_commands if resource_avail_commands else None,
#         }
#
#         # Add Many2one fields with create commands
#         # if staff_vals:
#         #     bookable_item_vals['staff_id'] = [(0, 0, staff_vals)]
#         if session_type_vals:
#             bookable_item_vals['session_type_id'] = [(0, 0, session_type_vals)]
#         if location_vals:
#             bookable_item_vals['location_id'] = [(0, 0, location_vals)]
#
#         return {k: v for k, v in bookable_item_vals.items() if v is not None and v is not False}
#
#     def _open_selection_wizard(self, limit=None, bookable_item_ids=None):
#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Select Session Types',
#             'res_model': 'session.type.selection.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {
#                 'default_limit': limit,
#                 'default_bookable_item_ids': bookable_item_ids,
#             }
#         }
#
#     def synchronize(self, session_type_ids=None, limit=None, bookable_item_ids=None):
#         """
#         Synchronize bookable items from Mindbody to Odoo.
#
#         Args:
#             limit (int, optional): Maximum number of records to fetch
#             bookable_item_ids (list, optional): Specific bookable item IDs to sync
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         if not session_type_ids:
#             return self._open_selection_wizard(limit, bookable_item_ids)
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             # Prepare parameters
#             params = {}
#             if limit:
#                 params['Limit'] = limit
#             if bookable_item_ids:
#                 params['BookableItemIDs'] = ','.join(map(str, bookable_item_ids)) if isinstance(bookable_item_ids,
#                                                                                                 list) else bookable_item_ids
#             if session_type_ids:
#                 params['SessionTypeIds'] = session_type_ids if isinstance(session_type_ids,
#                                                                           list) else session_type_ids.ids
#
#             _logger.info(f"Starting bookable item sync with params: {params}")
#
#             # Fetch bookable items from Mindbody API
#             response = api.get_appointment_bookableitems(params=params)
#             bookable_items_data = response.get('Availabilities', []) if isinstance(response, dict) else []
#
#             if not bookable_items_data:
#                 _logger.info("No bookable items found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(bookable_items_data)} bookable items from Mindbody")
#
#             # Process each bookable item
#             for bookable_item_data in bookable_items_data:
#                 try:
#                     bookable_item_id = bookable_item_data.get('Id')
#                     if not bookable_item_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping bookable item without ID")
#                         continue
#
#                     # Check if bookable item already exists
#                     existing = self.search([('bookable_item_id', '=', bookable_item_id)], limit=1)
#
#                     # Prepare bookable item values
#                     bookable_item_vals = self._prepare_bookable_item(bookable_item_data)
#                     print(bookable_item_vals)
#                     if existing:
#                         existing.write(bookable_item_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated bookable item {bookable_item_id}")
#                     else:
#                         self.create(bookable_item_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created bookable item {bookable_item_id}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing bookable item {bookable_item_data.get('Id')}: {str(e)}",
#                                   exc_info=True)
#                     raise ValueError(f"Bookable item sync failed: {str(e)}")
#
#             _logger.info(f"Bookable item sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync bookable items")
#             stats['errors'] += 1
#             raise UserError(f"Bookable item sync failed: {str(e)}")
#
#         return stats
