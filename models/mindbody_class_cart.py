import logging

_logger = logging.getLogger(__name__)
# mindbody_class_cart.py
from odoo import models, fields


class MindbodyClassCart(models.Model):
    _name = 'mindbody.class.cart'
    _description = 'Mindbody Class Cart'

    cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')

    class_schedule_id = fields.Integer(string='Class Schedule ID')
    visit_ids = fields.One2many('mindbody.visit.cart', 'class_cart_id', string='Visits')
    client_ids = fields.One2many('mindbody.client', 'class_cart_id', string='Clients')
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
    class_name = fields.Char(string='Class Name')
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

    # mindbody_class_cart.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_cart(self, data):
        """
        Prepare class cart values from API response.
        
        Args:
            data (dict): Class cart data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.class.cart create/write
        """
        self.ensure_one()

        # Prepare visits (One2many)
        visit_commands = []
        for visit_data in data.get('Visits', []):
            visit_vals = self.env['mindbody.visit.cart']._prepare_visit_cart(visit_data)
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

        class_cart_vals = {
            'class_schedule_id': data.get('ClassScheduleId'),
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
            'class_name': data.get('Name'),
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
            class_cart_vals['location_id'] = (0, 0, location_vals)
        if resource_vals:
            class_cart_vals['resource_id'] = (0, 0, resource_vals)
        if class_desc_vals:
            class_cart_vals['class_description_id'] = (0, 0, class_desc_vals)
        if staff_vals:
            class_cart_vals['staff_id'] = (0, 0, staff_vals)
        if booking_window_vals:
            class_cart_vals['booking_window_id'] = (0, 0, booking_window_vals)

        # Remove None values
        class_cart_vals = {k: v for k, v in class_cart_vals.items() if v is not None and v is not False}

        return class_cart_vals

    # mindbody_class_cart.py

    def synchronize(self, from_date=None, to_date=None, limit=None, class_cart_ids=None):
        """
        Synchronize class cart items from Mindbody to Odoo.
        Note: Class cart items are typically synced as part of shopping cart sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            class_cart_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Class cart items are synced automatically during shopping cart sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
