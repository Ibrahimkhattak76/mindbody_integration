import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyStaff(models.Model):
    _name = 'mindbody.staff'
    _description = 'Mindbody Staff'

    staff_id = fields.Integer(string='Staff ID', required=True)
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    display_name = fields.Char(string='Display Name')
    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    bio = fields.Text(string='Bio')
    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    postal_code = fields.Char(string='Postal Code')
    country = fields.Char(string='Country')
    work_phone = fields.Char(string='Work Phone')
    home_phone = fields.Char(string='Home Phone')
    mobile_phone = fields.Char(string='Mobile Phone')
    image_url = fields.Char(string='Image URL')

    appointment_instructor = fields.Boolean(string='Appointment Instructor')
    always_allow_double_booking = fields.Boolean(string='Always Allow Double Booking')
    independent_contractor = fields.Boolean(string='Independent Contractor')
    is_male = fields.Boolean(string='Is Male')
    class_teacher = fields.Boolean(string='Class Teacher')
    class_assistant = fields.Boolean(string='Class Assistant')
    class_assistant2 = fields.Boolean(string='Class Assistant 2')
    sort_order = fields.Integer(string='Sort Order')
    employment_start = fields.Datetime(string='Employment Start')
    employment_end = fields.Datetime(string='Employment End')
    provider_ids = fields.Char(string='Provider IDs')  # JSON list
    rep = fields.Boolean(string='Rep')
    rep2 = fields.Boolean(string='Rep 2')
    rep3 = fields.Boolean(string='Rep 3')
    rep4 = fields.Boolean(string='Rep 4')
    rep5 = fields.Boolean(string='Rep 5')
    rep6 = fields.Boolean(string='Rep 6')
    schedule_item_id = fields.Many2one('mindbody.schedule.item', string='Schedule Item')
    staff_settings_id = fields.Many2one('mindbody.staff.settings', string='Staff Settings')
    appointment_ids = fields.One2many('mindbody.staff.appointment', 'staff_id', string='Appointments')
    unavailability_ids = fields.One2many('mindbody.staff.unavailability', 'staff_id', string='Unavailabilities')
    availability_ids = fields.One2many('mindbody.staff.availability', 'staff_id', string='Availabilities')
    emp_id = fields.Char(string='Employee ID')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # For bookable items
    class_teacher = fields.Boolean(string='Class Teacher')

    # For login locations
    login_location_ids = fields.Many2many('mindbody.location', string='Login Locations')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff(self, data):
        """
        Prepare staff values from API response.

        Args:
            data (dict): Staff data from Mindbody API (from /staff/staff endpoint)

        Returns:
            dict: Values ready for mindbody.staff create/write
        """
        # Prepare staff settings (Many2one) - CREATE IT FIRST
        settings_id = False
        if data.get('StaffSettings'):
            settings_vals = self.env['mindbody.staff.settings']._prepare_staff_settings(data['StaffSettings'])
            if settings_vals:
                # Create the staff settings record
                settings = self.env['mindbody.staff.settings'].create(settings_vals)
                settings_id = settings.id

        # Prepare appointments (One2many)
        appointment_commands = []
        for appt_data in data.get('Appointments', []):
            appt_vals = self.env['mindbody.staff.appointment']._prepare_staff_appointment(appt_data)
            if appt_vals:
                appointment_commands.append((0, 0, appt_vals))

        # Prepare unavailabilities (One2many)
        unavail_commands = []
        for unavail_data in data.get('Unavailabilities', []):
            unavail_vals = self.env['mindbody.staff.unavailability']._prepare_staff_unavailability(unavail_data)
            if unavail_vals:
                unavail_commands.append((0, 0, unavail_vals))

        # Prepare availabilities (One2many)
        avail_commands = []
        for avail_data in data.get('Availabilities', []):
            avail_vals = self.env['mindbody.staff.availability']._prepare_staff_availability(avail_data)
            if avail_vals:
                avail_commands.append((0, 0, avail_vals))

        # Prepare login locations (Many2many)
        location_commands = []
        for loc_data in data.get('LoginLocations', []):
            loc_vals = self.env['mindbody.location']._prepare_location(loc_data)
            if loc_vals:
                # Check if location exists
                existing_loc = self.env['mindbody.location'].search([
                    ('location_id', '=', loc_data.get('Id'))
                ], limit=1)
                if existing_loc:
                    location_commands.append((4, existing_loc.id))
                else:
                    # Create the location first
                    new_loc = self.env['mindbody.location'].create(loc_vals)
                    location_commands.append((4, new_loc.id))

        staff_vals = {
            'staff_id': data.get('Id'),
            'first_name': data.get('FirstName'),
            'last_name': data.get('LastName'),
            'display_name': data.get('DisplayName'),
            'name': data.get('Name'),
            'email': data.get('Email'),
            'bio': data.get('Bio'),
            'address': data.get('Address'),
            'city': data.get('City'),
            'state': data.get('State'),
            'postal_code': data.get('PostalCode'),
            'country': data.get('Country'),
            'work_phone': data.get('WorkPhone'),
            'home_phone': data.get('HomePhone'),
            'mobile_phone': data.get('MobilePhone'),
            'image_url': data.get('ImageUrl'),
            'appointment_instructor': data.get('AppointmentInstructor', False),
            'always_allow_double_booking': data.get('AlwaysAllowDoubleBooking', False),
            'independent_contractor': data.get('IndependentContractor', False),
            'is_male': data.get('IsMale', False),
            'class_teacher': data.get('ClassTeacher', False),
            'class_assistant': data.get('ClassAssistant', False),
            'class_assistant2': data.get('ClassAssistant2', False),
            'sort_order': data.get('SortOrder', 0),
            'employment_start': data.get('EmploymentStart'),
            'employment_end': data.get('EmploymentEnd'),
            'provider_ids': str(data.get('ProviderIDs', [])),
            'rep': data.get('Rep', False),
            'rep2': data.get('Rep2', False),
            'rep3': data.get('Rep3', False),
            'rep4': data.get('Rep4', False),
            'rep5': data.get('Rep5', False),
            'rep6': data.get('Rep6', False),
            'emp_id': data.get('EmpID'),

            # Many2one field - use actual ID, not ORM command
            'staff_settings_id': settings_id,

            # One2many fields
            'appointment_ids': appointment_commands if appointment_commands else None,
            'unavailability_ids': unavail_commands if unavail_commands else None,
            'availability_ids': avail_commands if avail_commands else None,

            # Many2many fields
            'login_location_ids': location_commands if location_commands else None,
        }

        # Remove None values (but keep False for boolean fields)
        return {k: v for k, v in staff_vals.items() if v is not None}

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_ids=None):
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit

            _logger.info(f"Starting staff sync with params: {params}")

            # Fetch staff from Mindbody API
            response = api.get_staff_staff(params=params)
            _logger.info(f"Raw API response type: {type(response)}")
            _logger.info(f"Raw API response: {response}")

            staff_data = response.get('StaffMembers', []) if isinstance(response, dict) else []
            _logger.info(f"Found {len(staff_data)} staff members in response")

            if not staff_data:
                _logger.warning("No staff found to sync - check your API credentials and endpoint")
                return stats

            for staff_member_data in staff_data:
                try:
                    staff_id = staff_member_data.get('Id')
                    _logger.info(f"Processing staff ID: {staff_id}")

                    staff_vals = self._prepare_staff(staff_member_data)
                    _logger.info(f"Prepared values for staff {staff_id}: {staff_vals}")

                    existing = self.search([('staff_id', '=', staff_id)], limit=1)

                    if existing:
                        _logger.info(f"Updating existing staff {staff_id}")
                        existing.write(staff_vals)
                        stats['updated'] += 1
                    else:
                        _logger.info(f"Creating new staff {staff_id}")
                        record = self.create(staff_vals)
                        _logger.info(f"Created record ID: {record.id}")
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing staff {staff_member_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            _logger.info(f"Sync complete: {stats}")
            return stats

        except Exception as e:
            _logger.exception("Failed to sync staff")
            raise UserError(f"Staff sync failed: {str(e)}")

# import logging
#
# from odoo import models, fields
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyStaff(models.Model):
#     _name = 'mindbody.staff'
#     _description = 'Mindbody Staff'
#
#     staff_id = fields.Integer(string='Staff ID', required=True)
#     first_name = fields.Char(string='First Name')
#     last_name = fields.Char(string='Last Name')
#     display_name = fields.Char(string='Display Name')
#     name = fields.Char(string='Name')
#     email = fields.Char(string='Email')
#     bio = fields.Text(string='Bio')
#     address = fields.Char(string='Address')
#     city = fields.Char(string='City')
#     state = fields.Char(string='State')
#     postal_code = fields.Char(string='Postal Code')
#     country = fields.Char(string='Country')
#     work_phone = fields.Char(string='Work Phone')
#     home_phone = fields.Char(string='Home Phone')
#     mobile_phone = fields.Char(string='Mobile Phone')
#     image_url = fields.Char(string='Image URL')
#
#     appointment_instructor = fields.Boolean(string='Appointment Instructor')
#     always_allow_double_booking = fields.Boolean(string='Always Allow Double Booking')
#     independent_contractor = fields.Boolean(string='Independent Contractor')
#     is_male = fields.Boolean(string='Is Male')
#     class_teacher = fields.Boolean(string='Class Teacher')
#     class_assistant = fields.Boolean(string='Class Assistant')
#     class_assistant2 = fields.Boolean(string='Class Assistant 2')
#     sort_order = fields.Integer(string='Sort Order')
#     employment_start = fields.Datetime(string='Employment Start')
#     employment_end = fields.Datetime(string='Employment End')
#     provider_ids = fields.Char(string='Provider IDs')  # JSON list
#     rep = fields.Boolean(string='Rep')
#     rep2 = fields.Boolean(string='Rep 2')
#     rep3 = fields.Boolean(string='Rep 3')
#     rep4 = fields.Boolean(string='Rep 4')
#     rep5 = fields.Boolean(string='Rep 5')
#     rep6 = fields.Boolean(string='Rep 6')
#     schedule_item_id = fields.Many2one('mindbody.schedule.item', string='Schedule Item')
#     staff_settings_id = fields.Many2one('mindbody.staff.settings', string='Staff Settings')
#     appointment_ids = fields.One2many('mindbody.staff.appointment', 'staff_id', string='Appointments')
#     unavailability_ids = fields.One2many('mindbody.staff.unavailability', 'staff_id', string='Unavailabilities')
#     availability_ids = fields.One2many('mindbody.staff.availability', 'staff_id', string='Availabilities')
#     emp_id = fields.Char(string='Employee ID')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # For bookable items
#     class_teacher = fields.Boolean(string='Class Teacher')
#
#     # For login locations
#     login_location_ids = fields.Many2many('mindbody.location', string='Login Locations')
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_staff(self, data):
#         """
#         Prepare staff values from API response.
#
#         Args:
#             data (dict): Staff data from Mindbody API (from /staff/staff endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.staff create/write
#         """
#         # Prepare staff settings (Many2one)
#         settings_vals = None
#         if data.get('StaffSettings'):
#             settings_vals = self.env['mindbody.staff.settings']._prepare_staff_settings(data['StaffSettings'])
#
#         # Prepare appointments (One2many)
#         appointment_commands = []
#         for appt_data in data.get('Appointments', []):
#             appt_vals = self.env['mindbody.staff.appointment']._prepare_staff_appointment(appt_data)
#             if appt_vals:
#                 appointment_commands.append((0, 0, appt_vals))
#
#         # Prepare unavailabilities (One2many)
#         unavail_commands = []
#         for unavail_data in data.get('Unavailabilities', []):
#             unavail_vals = self.env['mindbody.staff.unavailability']._prepare_staff_unavailability(unavail_data)
#             if unavail_vals:
#                 unavail_commands.append((0, 0, unavail_vals))
#
#         # Prepare availabilities (One2many)
#         avail_commands = []
#         for avail_data in data.get('Availabilities', []):
#             avail_vals = self.env['mindbody.staff.availability']._prepare_staff_availability(avail_data)
#             if avail_vals:
#                 avail_commands.append((0, 0, avail_vals))
#
#         # Prepare login locations (Many2many)
#         location_commands = []
#         for loc_data in data.get('LoginLocations', []):
#             loc_vals = self.env['mindbody.location']._prepare_location(loc_data)
#             if loc_vals:
#                 # Check if location exists
#                 existing_loc = self.env['mindbody.location'].search([
#                     ('location_id', '=', loc_data.get('Id'))
#                 ], limit=1)
#                 if existing_loc:
#                     location_commands.append((4, existing_loc.id))
#                 else:
#                     location_commands.append((0, 0, loc_vals))
#
#         staff_vals = {
#             'staff_id': data.get('Id'),
#             'first_name': data.get('FirstName'),
#             'last_name': data.get('LastName'),
#             'display_name': data.get('DisplayName'),
#             'name': data.get('Name'),
#             'email': data.get('Email'),
#             'bio': data.get('Bio'),
#             'address': data.get('Address'),
#             'city': data.get('City'),
#             'state': data.get('State'),
#             'postal_code': data.get('PostalCode'),
#             'country': data.get('Country'),
#             'work_phone': data.get('WorkPhone'),
#             'home_phone': data.get('HomePhone'),
#             'mobile_phone': data.get('MobilePhone'),
#             'image_url': data.get('ImageUrl'),
#             'appointment_instructor': data.get('AppointmentInstructor', False),
#             'always_allow_double_booking': data.get('AlwaysAllowDoubleBooking', False),
#             'independent_contractor': data.get('IndependentContractor', False),
#             'is_male': data.get('IsMale', False),
#             'class_teacher': data.get('ClassTeacher', False),
#             'class_assistant': data.get('ClassAssistant', False),
#             'class_assistant2': data.get('ClassAssistant2', False),
#             'sort_order': data.get('SortOrder', 0),
#             'employment_start': data.get('EmploymentStart'),
#             'employment_end': data.get('EmploymentEnd'),
#             'provider_ids': str(data.get('ProviderIDs', [])),
#             'rep': data.get('Rep', False),
#             'rep2': data.get('Rep2', False),
#             'rep3': data.get('Rep3', False),
#             'rep4': data.get('Rep4', False),
#             'rep5': data.get('Rep5', False),
#             'rep6': data.get('Rep6', False),
#             'emp_id': data.get('EmpID'),
#
#             # One2many fields
#             'appointment_ids': appointment_commands if appointment_commands else None,
#             'unavailability_ids': unavail_commands if unavail_commands else None,
#             'availability_ids': avail_commands if avail_commands else None,
#
#             # Many2many fields
#             'login_location_ids': location_commands if location_commands else [(5, 0, 0)],
#         }
#
#         # Add Many2one fields with create commands
#         if settings_vals:
#             staff_vals['staff_settings_id'] = (0, 0, settings_vals)
#
#         return {k: v for k, v in staff_vals.items() if v is not None and v is not False}
#
#     # mindbody_staff.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, staff_ids=None):
#         """
#         Synchronize staff from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for modified staff
#             to_date (str, optional): End date for modified staff
#             limit (int, optional): Maximum number of records to fetch
#             staff_ids (list, optional): Specific staff IDs to sync
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
#             if staff_ids:
#                 params['StaffIDs'] = ','.join(map(str, staff_ids)) if isinstance(staff_ids, list) else staff_ids
#             if from_date:
#                 params['ModifiedDateTime'] = from_date
#                 if to_date:
#                     params['ModifiedDateTime'] = f"{from_date},{to_date}"
#
#             _logger.info(f"Starting staff sync with params: {params}")
#
#             # Fetch staff from Mindbody API
#             response = api.get_staff_staff(params=params)
#             staff_data = response.get('StaffMembers', []) if isinstance(response, dict) else []
#
#             if not staff_data:
#                 _logger.info("No staff found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(staff_data)} staff from Mindbody")
#
#             # Process each staff member
#             for staff_member_data in staff_data:
#                 try:
#                     staff_id = staff_member_data.get('Id')
#                     if not staff_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping staff without ID")
#                         continue
#
#                     # Check if staff already exists
#                     existing = self.search([('staff_id', '=', staff_id)], limit=1)
#
#                     # Prepare staff values
#                     staff_vals = self._prepare_staff(staff_member_data)
#
#                     if existing:
#                         existing.write(staff_vals)
#                         stats['updated'] += 1
#                         _logger.info(
#                             f"Updated staff {staff_id}: {staff_member_data.get('FirstName')} {staff_member_data.get('LastName')}")
#                     else:
#                         self.create(staff_vals)
#                         stats['created'] += 1
#                         _logger.info(
#                             f"Created staff {staff_id}: {staff_member_data.get('FirstName')} {staff_member_data.get('LastName')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing staff {staff_member_data.get('Id')}: {str(e)}", exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 self.env['mindbody.pagination.response'].create(
#                     self.env['mindbody.pagination.response']._prepare_pagination_response(
#                         response['PaginationResponse'])
#                 )
#
#             _logger.info(f"Staff sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync staff")
#             stats['errors'] += 1
#             raise UserError(f"Staff sync failed: {str(e)}")
#
#         return stats
