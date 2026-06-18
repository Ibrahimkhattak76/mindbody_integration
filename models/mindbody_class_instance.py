import logging

_logger = logging.getLogger(__name__)
# mindbody_class_instance.py
from odoo import models, fields


class MindbodyClassInstance(models.Model):
    _name = 'mindbody.class.instance'
    _description = 'Mindbody Class Instance'

    class_schedule_id = fields.Many2one('mindbody.class.schedule', string='Class Schedule')
    enrollment_id = fields.Many2one('mindbody.enrollment', string='Enrollment')
    class_schedule_id_int = fields.Integer(string='Class Schedule ID Integer')
    visit_ids = fields.One2many('mindbody.class.visit', 'class_instance_id', string='Visits')
    client_ids = fields.One2many('mindbody.client', 'class_instance_id', string='Clients')
    location_id = fields.Many2one('mindbody.location', string='Location')
    resource_id = fields.Many2one('mindbody.resource', string='Resource')
    max_capacity = fields.Integer(string='Max Capacity')
    web_capacity = fields.Integer(string='Web Capacity')
    total_booked = fields.Integer(string='Total Booked')
    total_signed_in = fields.Integer(string='Total Signed In')
    total_booked_waitlist = fields.Integer(string='Total Booked Waitlist')
    web_booked = fields.Integer(string='Web Booked')
    semester_id = fields.Integer(string='Semester ID')
    is_canceled = fields.Boolean(string='Is Canceled')
    substitute = fields.Boolean(string='Substitute')
    active = fields.Boolean(string='Active')
    is_waitlist_available = fields.Boolean(string='Is Waitlist Available')
    is_enrolled = fields.Boolean(string='Is Enrolled')
    hide_cancel = fields.Boolean(string='Hide Cancel')
    class_id = fields.Integer(string='Class ID')
    is_available = fields.Boolean(string='Is Available')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    last_modified_date_time = fields.Datetime(string='Last Modified Date Time')
    class_description_id = fields.Many2one('mindbody.class.description', string='Class Description')
    staff_id = fields.Many2one('mindbody.staff', string='Staff')
    booking_window_id = fields.Many2one('mindbody.booking.window', string='Booking Window')
    booking_status = fields.Selection([
        ('PaymentRequired', 'Payment Required')
    ], string='Booking Status')
    virtual_stream_link = fields.Char(string='Virtual Stream Link')
    wait_list_size = fields.Integer(string='Wait List Size')
    class_notes = fields.Text(string='Class Notes')
    theme_name = fields.Char(string='Theme Name')

    # mindbody_class_instance.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_instance(self, data):
        """
        Prepare class instance values from API response.
        
        Args:
            data (dict): Class instance data from Mindbody API (from /class/classes endpoint)
            
        Returns:
            dict: Values ready for mindbody.class.instance create/write
        """
        self.ensure_one()

        # Prepare visits (One2many)
        visit_commands = []
        for visit_data in data.get('Visits', []):
            visit_vals = self.env['mindbody.class.visit']._prepare_class_visit(visit_data)
            if visit_vals:
                visit_commands.append((0, 0, visit_vals))

        # Prepare clients (One2many)
        client_commands = []
        for client_data in data.get('Clients', []):
            client_vals = self.env['mindbody.client']._prepare_client(client_data)
            if client_vals:
                client_commands.append((0, 0, client_vals))

        # Prepare location (Many2one)
        location_vals = None
        if data.get('Location'):
            location_vals = self.env['mindbody.location']._prepare_location(data['Location'])

        # Prepare resource (Many2one)
        resource_vals = None
        if data.get('Resource'):
            resource_vals = self.env['mindbody.resource']._prepare_resource(data['Resource'])

        # Prepare class description (Many2one)
        class_desc_vals = None
        if data.get('ClassDescription'):
            class_desc_vals = self.env['mindbody.class.description']._prepare_class_description(
                data['ClassDescription'])

        # Prepare staff (Many2one)
        staff_vals = None
        if data.get('Staff'):
            staff_vals = self.env['mindbody.staff']._prepare_staff(data['Staff'])

        # Prepare booking window (Many2one)
        booking_window_vals = None
        if data.get('BookingWindow'):
            booking_window_vals = self.env['mindbody.booking.window']._prepare_booking_window(data['BookingWindow'])

        class_instance_vals = {
            'class_schedule_id_int': data.get('ClassScheduleId'),
            'max_capacity': data.get('MaxCapacity', 0),
            'web_capacity': data.get('WebCapacity', 0),
            'total_booked': data.get('TotalBooked', 0),
            'total_signed_in': data.get('TotalSignedIn', 0),
            'total_booked_waitlist': data.get('TotalBookedWaitlist', 0),
            'web_booked': data.get('WebBooked', 0),
            'semester_id': data.get('SemesterId'),
            'is_canceled': data.get('IsCanceled', False),
            'substitute': data.get('Substitute', False),
            'active': data.get('Active', True),
            'is_waitlist_available': data.get('IsWaitlistAvailable', False),
            'is_enrolled': data.get('IsEnrolled', False),
            'hide_cancel': data.get('HideCancel', False),
            'class_id': data.get('Id'),
            'is_available': data.get('IsAvailable', False),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'last_modified_date_time': data.get('LastModifiedDateTime'),
            'booking_status': data.get('BookingStatus'),
            'virtual_stream_link': data.get('VirtualStreamLink'),
            'wait_list_size': data.get('WaitListSize', 0),
            'class_notes': data.get('ClassNotes'),
            'theme_name': data.get('ThemeName'),

            # One2many fields
            'visit_ids': visit_commands if visit_commands else None,
            'client_ids': client_commands if client_commands else [(5, 0, 0)],
        }

        # Add Many2one fields with create commands
        if location_vals:
            class_instance_vals['location_id'] = (0, 0, location_vals)
        if resource_vals:
            class_instance_vals['resource_id'] = (0, 0, resource_vals)
        if class_desc_vals:
            class_instance_vals['class_description_id'] = (0, 0, class_desc_vals)
        if staff_vals:
            class_instance_vals['staff_id'] = (0, 0, staff_vals)
        if booking_window_vals:
            class_instance_vals['booking_window_id'] = (0, 0, booking_window_vals)

        # Remove None values
        class_instance_vals = {k: v for k, v in class_instance_vals.items() if v is not None and v is not False}

        return class_instance_vals

    # mindbody_class_instance.py

    def synchronize(self, from_date=None, to_date=None, limit=None, class_instance_ids=None):
        """
        Synchronize class instances from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for class instances
            to_date (str, optional): End date for class instances
            limit (int, optional): Maximum number of records to fetch
            class_instance_ids (list, optional): Specific class instance IDs to sync
            
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
            if class_instance_ids:
                params['ClassInstanceIDs'] = ','.join(map(str, class_instance_ids)) if isinstance(class_instance_ids,
                                                                                                  list) else class_instance_ids
            if from_date:
                params['StartDateTime'] = from_date
                if to_date:
                    params['EndDateTime'] = to_date

            _logger.info(f"Starting class instance sync with params: {params}")

            # Fetch class instances from Mindbody API
            response = api.get_class_classes(params=params)
            classes_data = response.get('Classes', []) if isinstance(response, dict) else []

            if not classes_data:
                _logger.info("No class instances found to sync")
                return stats

            _logger.info(f"Fetched {len(classes_data)} class instances from Mindbody")

            # Process each class instance
            for class_data in classes_data:
                try:
                    class_id = class_data.get('Id')
                    if not class_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping class instance without ID")
                        continue

                    # Check if class instance already exists
                    existing = self.search([('class_id', '=', class_id)], limit=1)

                    # Prepare class instance values
                    class_vals = self._prepare_class_instance(class_data)

                    if existing:
                        existing.write(class_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated class instance {class_id}")
                    else:
                        self.create(class_vals)
                        stats['created'] += 1
                        _logger.info(f"Created class instance {class_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing class instance {class_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Class instance sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync class instances")
            stats['errors'] += 1
            raise UserError(f"Class instance sync failed: {str(e)}")

        return stats
