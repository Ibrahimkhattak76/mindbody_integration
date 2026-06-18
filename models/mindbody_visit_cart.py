import logging

_logger = logging.getLogger(__name__)
# mindbody_visit_cart.py
from odoo import models, fields


class MindbodyVisitCart(models.Model):
    _name = 'mindbody.visit.cart'
    _description = 'Mindbody Visit Cart'

    class_cart_id = fields.Many2one('mindbody.class.cart', string='Class Cart')

    appointment_id = fields.Integer(string='Appointment ID')
    appointment_gender_preference = fields.Selection([
        ('None', 'None'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ], string='Appointment Gender Preference', default='None')
    appointment_status = fields.Selection([
        ('None', 'None'),
        ('Booked', 'Booked'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Arrived', 'Arrived'),
        ('NoShow', 'No Show'),
        ('Cancelled', 'Cancelled'),
        ('LateCancelled', 'Late Cancelled')
    ], string='Appointment Status', default='None')
    class_id = fields.Integer(string='Class ID')
    client_id = fields.Char(string='Client ID')
    client_photo_url = fields.Char(string='Client Photo URL')
    client_unique_id = fields.Integer(string='Client Unique ID')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    visit_id = fields.Integer(string='Visit ID')
    last_modified_date_time = fields.Datetime(string='Last Modified Date Time')
    late_cancelled = fields.Boolean(string='Late Cancelled')
    site_id = fields.Integer(string='Site ID')
    location_id = fields.Integer(string='Location ID')
    make_up = fields.Boolean(string='Make Up')
    name = fields.Char(string='Name')
    service_id = fields.Integer(string='Service ID')
    service_name = fields.Char(string='Service Name')
    service_id_ref = fields.Many2one('mindbody.service', string='Service')
    product_id = fields.Integer(string='Product ID')
    signed_in = fields.Boolean(string='Signed In')
    staff_id = fields.Integer(string='Staff ID')
    web_signup = fields.Boolean(string='Web Signup')
    action = fields.Selection([
        ('None', 'None'),
        ('Added', 'Added'),
        ('Updated', 'Updated'),
        ('Failed', 'Failed'),
        ('Removed', 'Removed')
    ], string='Action', default='None')
    missed = fields.Boolean(string='Missed')
    visit_type = fields.Integer(string='Visit Type')
    type_group = fields.Integer(string='Type Group')
    type_taken = fields.Char(string='Type Taken')

    # For add client to class response
    cross_regional_booking_performed = fields.Boolean(string='Cross Regional Booking Performed')
    waitlist_entry_id = fields.Integer(string='Waitlist Entry ID')

    # mindbody_visit_cart.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_visit_cart(self, data):
        """
        Prepare visit cart values from API response.
        
        Args:
            data (dict): Visit cart data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.visit.cart create/write
        """
        self.ensure_one()

        # Prepare service (Many2one)
        service_vals = None
        if data.get('Service'):
            service_vals = self.env['mindbody.service']._prepare_service(data['Service'])

        visit_cart_vals = {
            'appointment_id': data.get('AppointmentId', 0),
            'appointment_gender_preference': data.get('AppointmentGenderPreference', 'None'),
            'appointment_status': data.get('AppointmentStatus', 'None'),
            'class_id': data.get('ClassId'),
            'client_id': data.get('ClientId'),
            'client_photo_url': data.get('ClientPhotoUrl'),
            'client_unique_id': data.get('ClientUniqueId', 0),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'visit_id': data.get('Id', 0),
            'last_modified_date_time': data.get('LastModifiedDateTime'),
            'late_cancelled': data.get('LateCancelled', False),
            'site_id': data.get('SiteId'),
            'location_id': data.get('LocationId'),
            'make_up': data.get('MakeUp', False),
            'name': data.get('Name'),
            'service_id': data.get('ServiceId'),
            'service_name': data.get('ServiceName'),
            'product_id': data.get('ProductId'),
            'signed_in': data.get('SignedIn', False),
            'staff_id': data.get('StaffId'),
            'web_signup': data.get('WebSignup', False),
            'action': data.get('Action', 'None'),
            'missed': data.get('Missed', False),
            'visit_type': data.get('VisitType', 0),
            'type_group': data.get('TypeGroup', 0),
            'type_taken': data.get('TypeTaken'),
            'cross_regional_booking_performed': data.get('CrossRegionalBookingPerformed', False),
            'waitlist_entry_id': data.get('WaitlistEntryId', 0),
        }

        # Add Many2one fields with create commands
        if service_vals:
            visit_cart_vals['service_id_ref'] = (0, 0, service_vals)

        # Remove None values
        visit_cart_vals = {k: v for k, v in visit_cart_vals.items() if v is not None and v is not False}

        return visit_cart_vals

    # mindbody_visit_cart.py

    def synchronize(self, from_date=None, to_date=None, limit=None, visit_cart_ids=None):
        """
        Synchronize visit cart items from Mindbody to Odoo.
        Note: Visit cart items are typically synced as part of shopping cart sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            visit_cart_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Visit cart items are synced automatically during shopping cart sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
