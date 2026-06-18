import logging
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyAppointmentCart(models.Model):
    _name = 'mindbody.appointment.cart'
    _description = 'Mindbody Appointment Cart'

    cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')
    cart_item_id = fields.Many2one('mindbody.cart.item', string='Cart Item')
    gender_preference = fields.Selection([
        ('None', 'None'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ], string='Gender Preference', default='None')
    duration = fields.Integer(string='Duration')
    provider_id = fields.Char(string='Provider ID')
    appointment_id = fields.Integer(string='Appointment ID')
    status = fields.Selection([
        ('None', 'None'),
        ('Booked', 'Booked'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Arrived', 'Arrived'),
        ('NoShow', 'No Show'),
        ('Cancelled', 'Cancelled'),
        ('LateCancelled', 'Late Cancelled')
    ], string='Status', default='None')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    notes = fields.Text(string='Notes')
    partner_external_id = fields.Char(string='Partner External ID')
    staff_requested = fields.Boolean(string='Staff Requested')
    program_id = fields.Integer(string='Program ID')
    session_type_id = fields.Integer(string='Session Type ID')
    location_id = fields.Integer(string='Location ID')
    staff_external_id = fields.Integer(string='Staff ID')
    staff_id = fields.Many2one('mindbody.staff', string='Staff')
    client_id = fields.Char(string='Client ID')
    first_appointment = fields.Boolean(string='First Appointment')
    is_waitlist = fields.Boolean(string='Is Waitlist')
    waitlist_entry_id = fields.Integer(string='Waitlist Entry ID')
    client_service_id = fields.Integer(string='Client Service ID')
    resource_ids = fields.One2many('mindbody.appointment.resource', 'appointment_cart_id', string='Resources')
    add_on_ids = fields.One2many('mindbody.appointment.add.on', 'appointment_cart_id', string='Add Ons')
    online_description = fields.Text(string='Online Description')
    preparation_time = fields.Integer(string='Preparation Time')
    finish_time = fields.Integer(string='Finish Time')

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

    def _prepare_appointment_cart(self, data):
        """Prepare appointment cart values from API response"""
        resource_commands = []
        for res_data in data.get('Resources', []):
            res_vals = self.env['mindbody.appointment.resource']._prepare_appointment_resource(res_data)
            if res_vals:
                resource_commands.append((0, 0, res_vals))

        addon_commands = []
        for addon_data in data.get('AddOns', []):
            addon_vals = self.env['mindbody.appointment.add.on']._prepare_appointment_add_on(addon_data)
            if addon_vals:
                addon_commands.append((0, 0, addon_vals))

        appointment_cart_vals = {
            'gender_preference': data.get('GenderPreference', 'None'),
            'duration': data.get('Duration', 0),
            'provider_id': data.get('ProviderId'),
            'appointment_id': data.get('Id', 0),
            'status': data.get('Status', 'None'),
            'start_date_time': self._parse_datetime(data.get('StartDateTime')),
            'end_date_time': self._parse_datetime(data.get('EndDateTime')),
            'notes': data.get('Notes'),
            'partner_external_id': data.get('PartnerExternalId'),
            'staff_requested': data.get('StaffRequested', False),
            'program_id': data.get('ProgramId'),
            'session_type_id': data.get('SessionTypeId'),
            'location_id': data.get('LocationId'),
            'staff_external_id': data.get('StaffId'),
            'client_id': data.get('ClientId'),
            'first_appointment': data.get('FirstAppointment', False),
            'is_waitlist': data.get('IsWaitlist', False),
            'waitlist_entry_id': data.get('WaitlistEntryId', 0),
            'client_service_id': data.get('ClientServiceId', 0),
            'online_description': data.get('OnlineDescription'),
            'preparation_time': data.get('PreparationTime', 0),
            'finish_time': data.get('FinishTime', 0),
        }

        if resource_commands:
            appointment_cart_vals['resource_ids'] = resource_commands
        if addon_commands:
            appointment_cart_vals['add_on_ids'] = addon_commands

        return {k: v for k, v in appointment_cart_vals.items() if v is not None and v is not False}

    def synchronize(self):
        """Delegate to Shopping Cart sync"""
        _logger.info("Appointment cart items are synced automatically during shopping cart sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

# import logging
#
# _logger = logging.getLogger(__name__)
# # mindbody_appointment_cart.py
# from odoo import models, fields
#
#
# class MindbodyAppointmentCart(models.Model):
#     _name = 'mindbody.appointment.cart'
#     _description = 'Mindbody Appointment Cart'
#
#     cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')
#     cart_item_id = fields.Many2one('mindbody.cart.item', string='Cart Item')
#
#     gender_preference = fields.Selection([
#         ('None', 'None'),
#         ('Male', 'Male'),
#         ('Female', 'Female')
#     ], string='Gender Preference', default='None')
#     duration = fields.Integer(string='Duration')
#     provider_id = fields.Char(string='Provider ID')
#     appointment_id = fields.Integer(string='Appointment ID')
#     status = fields.Selection([
#         ('None', 'None'),
#         ('Booked', 'Booked'),
#         ('Confirmed', 'Confirmed'),
#         ('Completed', 'Completed'),
#         ('Arrived', 'Arrived'),
#         ('NoShow', 'No Show'),
#         ('Cancelled', 'Cancelled'),
#         ('LateCancelled', 'Late Cancelled')
#     ], string='Status', default='None')
#     start_date_time = fields.Datetime(string='Start Date Time')
#     end_date_time = fields.Datetime(string='End Date Time')
#     notes = fields.Text(string='Notes')
#     partner_external_id = fields.Char(string='Partner External ID')
#     staff_requested = fields.Boolean(string='Staff Requested')
#     program_id = fields.Integer(string='Program ID')
#     session_type_id = fields.Integer(string='Session Type ID')
#     location_id = fields.Integer(string='Location ID')
#     staff_external_id = fields.Integer(string='Staff ID')
#     staff_id = fields.Many2one('mindbody.staff', string='Staff')
#     client_id = fields.Char(string='Client ID')
#     first_appointment = fields.Boolean(string='First Appointment')
#     is_waitlist = fields.Boolean(string='Is Waitlist')
#     waitlist_entry_id = fields.Integer(string='Waitlist Entry ID')
#     client_service_id = fields.Integer(string='Client Service ID')
#     resource_ids = fields.One2many('mindbody.appointment.resource', 'appointment_cart_id', string='Resources')
#     add_on_ids = fields.One2many('mindbody.appointment.add.on', 'appointment_cart_id', string='Add Ons')
#     online_description = fields.Text(string='Online Description')
#     preparation_time = fields.Integer(string='Preparation Time')
#     finish_time = fields.Integer(string='Finish Time')
#
#     # mindbody_appointment_cart.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_appointment_cart(self, data):
#         """
#         Prepare appointment cart values from API response.
#
#         Args:
#             data (dict): Appointment cart data from Mindbody API
#
#         Returns:
#             dict: Values ready for mindbody.appointment.cart create/write
#         """
#
#         # Prepare staff name (Many2one)
#         staff_vals = None
#         if data.get('Staff'):
#             staff_vals = self.env['mindbody.staff.name']._prepare_staff_name(data['Staff'])
#
#         # Prepare resources (One2many)
#         resource_commands = []
#         for res_data in data.get('Resources', []):
#             res_vals = self.env['mindbody.appointment.resource']._prepare_appointment_resource(res_data)
#             if res_vals:
#                 resource_commands.append((0, 0, res_vals))
#
#         # Prepare add-ons (One2many)
#         addon_commands = []
#         for addon_data in data.get('AddOns', []):
#             addon_vals = self.env['mindbody.appointment.add.on']._prepare_appointment_add_on(addon_data)
#             if addon_vals:
#                 addon_commands.append((0, 0, addon_vals))
#
#         appointment_cart_vals = {
#             'gender_preference': data.get('GenderPreference', 'None'),
#             'duration': data.get('Duration', 0),
#             'provider_id': data.get('ProviderId'),
#             'appointment_id': data.get('Id', 0),
#             'status': data.get('Status', 'None'),
#             'start_date_time': data.get('StartDateTime'),
#             'end_date_time': data.get('EndDateTime'),
#             'notes': data.get('Notes'),
#             'partner_external_id': data.get('PartnerExternalId'),
#             'staff_requested': data.get('StaffRequested', False),
#             'program_id': data.get('ProgramId'),
#             'session_type_id': data.get('SessionTypeId'),
#             'location_id': data.get('LocationId'),
#             'staff_external_id': data.get('StaffId'),
#             'client_id': data.get('ClientId'),
#             'first_appointment': data.get('FirstAppointment', False),
#             'is_waitlist': data.get('IsWaitlist', False),
#             'waitlist_entry_id': data.get('WaitlistEntryId', 0),
#             'client_service_id': data.get('ClientServiceId', 0),
#             'online_description': data.get('OnlineDescription'),
#             'preparation_time': data.get('PreparationTime', 0),
#             'finish_time': data.get('FinishTime', 0),
#
#             # One2many fields
#             'resource_ids': resource_commands if resource_commands else None,
#             'add_on_ids': addon_commands if addon_commands else None,
#         }
#
#         # Add Many2one fields with create commands
#         if staff_vals:
#             appointment_cart_vals['staff_id'] = (0, 0, staff_vals)
#
#         # Remove None values
#         appointment_cart_vals = {k: v for k, v in appointment_cart_vals.items() if v is not None and v is not False}
#
#         return appointment_cart_vals
#
#     def synchronize(self):
#         """
#         Synchronize appointment cart items from Mindbody to Odoo.
#         Note: Appointment cart items are typically synced as part of shopping cart sync.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Not used for this endpoint
#             appointment_cart_ids (list, optional): Not used for this endpoint
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         _logger.info("Appointment cart items are synced automatically during shopping cart sync")
#         return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
