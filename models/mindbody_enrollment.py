# mindbody_enrollment.py
from odoo import models, fields


class MindbodyEnrollment(models.Model):
    _name = 'mindbody.enrollment'
    _description = 'Mindbody Enrollment'

    enrollment_id = fields.Integer(string='Enrollment ID')
    name = fields.Char(string='Name')
    class_ids = fields.One2many('mindbody.class.instance', 'enrollment_id', string='Classes')
    client_ids = fields.One2many('mindbody.client', 'enrollment_id', string='Clients')
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
    frequency_type = fields.Selection([
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly')
    ], string='Frequency Type', default='Daily')
    frequency_interval = fields.Integer(string='Frequency Interval')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')

    # For add client to enrollment response
    class_instance_ids = fields.One2many('mindbody.class.instance', 'enrollment_id', string='Class Instances')
    clients = fields.One2many('mindbody.client', 'enrollment_id', string='Clients')
    course_obj = fields.Many2one('mindbody.course', string='Course Object')
    semester_id_int = fields.Integer(string='Semester ID Integer')
    is_available_bool = fields.Boolean(string='Is Available Boolean')
    id_int = fields.Integer(string='ID Integer')
    class_description_obj = fields.Many2one('mindbody.class.description', string='Class Description Object')
    day_sunday_bool = fields.Boolean(string='Day Sunday Boolean')
    day_monday_bool = fields.Boolean(string='Day Monday Boolean')
    day_tuesday_bool = fields.Boolean(string='Day Tuesday Boolean')
    day_wednesday_bool = fields.Boolean(string='Day Wednesday Boolean')
    day_thursday_bool = fields.Boolean(string='Day Thursday Boolean')
    day_friday_bool = fields.Boolean(string='Day Friday Boolean')
    day_saturday_bool = fields.Boolean(string='Day Saturday Boolean')
    allow_open_enrollment_bool = fields.Boolean(string='Allow Open Enrollment Boolean')
    allow_date_forward_enrollment_bool = fields.Boolean(string='Allow Date Forward Enrollment Boolean')
    start_time_dt = fields.Datetime(string='Start Time Datetime')
    end_time_dt = fields.Datetime(string='End Time Datetime')
    start_date_dt = fields.Datetime(string='Start Date Datetime')
    end_date_dt = fields.Datetime(string='End Date Datetime')
    staff_obj = fields.Many2one('mindbody.staff', string='Staff Object')
    location_obj = fields.Many2one('mindbody.location', string='Location Object')

    # mindbody_enrollment.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_enrollment(self, data):
        """
        Prepare enrollment values from API response.
        
        Args:
            data (dict): Enrollment data from Mindbody API (from /enrollment/enrollments endpoint)
            
        Returns:
            dict: Values ready for mindbody.enrollment create/write
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

        enrollment_vals = {
            'enrollment_id': data.get('Id'),
            'name': data.get('Name'),
            'semester_id_int': data.get('SemesterId'),
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
            'frequency_type': data.get('FrequencyType', 'Daily'),
            'frequency_interval': data.get('FrequencyInterval', 0),

            # Additional fields for add client to enrollment response
            'semester_id_int': data.get('SemesterId'),
            'is_available_bool': data.get('IsAvailable', False),
            'id_int': data.get('Id'),
            'day_sunday_bool': data.get('DaySunday', False),
            'day_monday_bool': data.get('DayMonday', False),
            'day_tuesday_bool': data.get('DayTuesday', False),
            'day_wednesday_bool': data.get('DayWednesday', False),
            'day_thursday_bool': data.get('DayThursday', False),
            'day_friday_bool': data.get('DayFriday', False),
            'day_saturday_bool': data.get('DaySaturday', False),
            'allow_open_enrollment_bool': data.get('AllowOpenEnrollment', False),
            'allow_date_forward_enrollment_bool': data.get('AllowDateForwardEnrollment', False),
            'start_time_dt': data.get('StartTime'),
            'end_time_dt': data.get('EndTime'),
            'start_date_dt': data.get('StartDate'),
            'end_date_dt': data.get('EndDate'),

            # One2many fields
            'class_ids': class_commands if class_commands else None,
            'client_ids': client_commands if client_commands else [(5, 0, 0)],
            'class_instance_ids': class_commands if class_commands else None,
            'clients': client_commands if client_commands else [(5, 0, 0)],
        }

        # Add Many2one fields with create commands
        if course_vals:
            enrollment_vals['course_id'] = (0, 0, course_vals)
            enrollment_vals['course_obj'] = (0, 0, course_vals)
        if class_desc_vals:
            enrollment_vals['class_description_id'] = (0, 0, class_desc_vals)
            enrollment_vals['class_description_obj'] = (0, 0, class_desc_vals)
        if staff_vals:
            enrollment_vals['staff_id'] = (0, 0, staff_vals)
            enrollment_vals['staff_obj'] = (0, 0, staff_vals)
        if location_vals:
            enrollment_vals['location_id'] = (0, 0, location_vals)
            enrollment_vals['location_obj'] = (0, 0, location_vals)
        if pagination_vals:
            enrollment_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        enrollment_vals = {k: v for k, v in enrollment_vals.items() if v is not None and v is not False}

        return enrollment_vals
