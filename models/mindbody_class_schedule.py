import logging

_logger = logging.getLogger(__name__)
# mindbody_class_schedule.py
from odoo import models, fields


class MindbodyClassSchedule(models.Model):
    _name = 'mindbody.class.schedule'
    _description = 'Mindbody Class Schedule'

    class_schedule_id = fields.Integer(string='Class Schedule ID')
    class_ids = fields.One2many('mindbody.class.instance', 'class_schedule_id', string='Classes')
    client_ids = fields.One2many('mindbody.client', 'class_schedule_id', string='Clients')
    course_id = fields.Many2one('mindbody.course', string='Course')
    semester_id = fields.Integer(string='Semester ID')
    is_available = fields.Boolean(string='Is Available')
    external_id = fields.Integer(string='ID')
    class_description_id = fields.Many2one('mindbody.class.description', string='Class Description')
    day_sunday = fields.Boolean(string='Day Sunday')
    day_monday = fields.Boolean(string='Day Monday')
    day_tuesday = fields.Boolean(string='Day Tuesday')
    day_wednesday = fields.Boolean(string='Day Wednesday')
    day_thursday = fields.Boolean(string='Day Thursday')
    day_friday = fields.Boolean(string='Day Friday')
    day_saturday = fields.Boolean(string='Day Saturday')
    allow_open_enrollment = fields.Boolean(string='Allow Open Enrollment')
    allow_date_forward_enrollment = fields.Boolean(string='Allow Date Forward Enrollment')
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    staff_id = fields.Many2one('mindbody.staff', string='Staff')
    location_id = fields.Many2one('mindbody.location', string='Location')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_class_schedule.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_schedule(self, data):
        """
        Prepare class schedule values from API response.
        
        Args:
            data (dict): Class schedule data from Mindbody API (from /class/classschedules endpoint)
            
        Returns:
            dict: Values ready for mindbody.class.schedule create/write
        """
        self.ensure_one()

        # Prepare classes (One2many)
        class_commands = []
        for class_data in data.get('Classes', []):
            class_vals = self.env['mindbody.class.instance']._prepare_class_instance(class_data)
            if class_vals:
                class_commands.append((0, 0, class_vals))

        # Prepare clients (One2many)
        client_commands = []
        for client_data in data.get('Clients', []):
            client_vals = self.env['mindbody.client']._prepare_client(client_data)
            if client_vals:
                client_commands.append((0, 0, client_vals))

        # Prepare course (Many2one)
        course_vals = None
        if data.get('Course'):
            course_vals = self.env['mindbody.course']._prepare_course(data['Course'])

        # Prepare class description (Many2one)
        class_desc_vals = None
        if data.get('ClassDescription'):
            class_desc_vals = self.env['mindbody.class.description']._prepare_class_description(
                data['ClassDescription'])

        # Prepare staff (Many2one)
        staff_vals = None
        if data.get('Staff'):
            staff_vals = self.env['mindbody.staff']._prepare_staff(data['Staff'])

        # Prepare location (Many2one)
        location_vals = None
        if data.get('Location'):
            location_vals = self.env['mindbody.location']._prepare_location(data['Location'])

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        schedule_vals = {
            'class_schedule_id': data.get('Id'),
            'semester_id': data.get('SemesterId'),
            'is_available': data.get('IsAvailable', False),
            'day_sunday': data.get('DaySunday', False),
            'day_monday': data.get('DayMonday', False),
            'day_tuesday': data.get('DayTuesday', False),
            'day_wednesday': data.get('DayWednesday', False),
            'day_thursday': data.get('DayThursday', False),
            'day_friday': data.get('DayFriday', False),
            'day_saturday': data.get('DaySaturday', False),
            'allow_open_enrollment': data.get('AllowOpenEnrollment', False),
            'allow_date_forward_enrollment': data.get('AllowDateForwardEnrollment', False),
            'start_time': data.get('StartTime'),
            'end_time': data.get('EndTime'),
            'start_date': data.get('StartDate'),
            'end_date': data.get('EndDate'),

            # One2many fields
            'class_ids': class_commands if class_commands else None,
            'client_ids': client_commands if client_commands else [(5, 0, 0)],
        }

        # Add Many2one fields with create commands
        if course_vals:
            schedule_vals['course_id'] = (0, 0, course_vals)
        if class_desc_vals:
            schedule_vals['class_description_id'] = (0, 0, class_desc_vals)
        if staff_vals:
            schedule_vals['staff_id'] = (0, 0, staff_vals)
        if location_vals:
            schedule_vals['location_id'] = (0, 0, location_vals)
        if pagination_vals:
            schedule_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        schedule_vals = {k: v for k, v in schedule_vals.items() if v is not None and v is not False}

        return schedule_vals

    # mindbody_class_schedule.py

    def synchronize(self, from_date=None, to_date=None, limit=None, class_schedule_ids=None):
        """
        Synchronize class schedules from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for class schedules
            to_date (str, optional): End date for class schedules
            limit (int, optional): Maximum number of records to fetch
            class_schedule_ids (list, optional): Specific class schedule IDs to sync
            
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
            if class_schedule_ids:
                params['ClassScheduleIDs'] = ','.join(map(str, class_schedule_ids)) if isinstance(class_schedule_ids,
                                                                                                  list) else class_schedule_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            _logger.info(f"Starting class schedule sync with params: {params}")

            # Fetch class schedules from Mindbody API
            response = api.get_class_classschedules(params=params)
            class_schedules_data = response.get('ClassSchedules', []) if isinstance(response, dict) else []

            if not class_schedules_data:
                _logger.info("No class schedules found to sync")
                return stats

            _logger.info(f"Fetched {len(class_schedules_data)} class schedules from Mindbody")

            # Process each class schedule
            for class_schedule_data in class_schedules_data:
                try:
                    class_schedule_id = class_schedule_data.get('Id')
                    if not class_schedule_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping class schedule without ID")
                        continue

                    # Check if class schedule already exists
                    existing = self.search([('class_schedule_id', '=', class_schedule_id)], limit=1)

                    # Prepare class schedule values
                    class_schedule_vals = self._prepare_class_schedule(class_schedule_data)

                    if existing:
                        existing.write(class_schedule_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated class schedule {class_schedule_id}")
                    else:
                        self.create(class_schedule_vals)
                        stats['created'] += 1
                        _logger.info(f"Created class schedule {class_schedule_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing class schedule {class_schedule_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Class schedule sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync class schedules")
            stats['errors'] += 1
            raise UserError(f"Class schedule sync failed: {str(e)}")

        return stats
