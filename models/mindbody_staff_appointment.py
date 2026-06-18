import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_appointment.py
from odoo import models, fields


class MindbodyStaffAppointment(models.Model):
    _name = 'mindbody.staff.appointment'
    _description = 'Mindbody Staff Appointment'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

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
    staff_id_int = fields.Integer(string='Staff ID Integer')
    staff_name_id = fields.Many2one('mindbody.staff.name', string='Staff Name')
    client_id = fields.Char(string='Client ID')
    first_appointment = fields.Boolean(string='First Appointment')
    is_waitlist = fields.Boolean(string='Is Waitlist')
    waitlist_entry_id = fields.Integer(string='Waitlist Entry ID')
    client_service_id = fields.Integer(string='Client Service ID')
    resource_ids = fields.One2many('mindbody.appointment.resource', 'staff_appointment_id', string='Resources')
    add_on_ids = fields.One2many('mindbody.appointment.add.on', 'staff_appointment_id', string='Add Ons')
    online_description = fields.Text(string='Online Description')

    # mindbody_staff_appointment.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_appointment(self, data):
        """
        Prepare staff appointment values from API response.
        
        Args:
            data (dict): Staff appointment data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.staff.appointment create/write
        """
        # Prepare staff name (Many2one)
        staff_name_vals = None
        if data.get('Staff'):
            staff_name_vals = self.env['mindbody.staff.name']._prepare_staff_name(data['Staff'])

        # Prepare resources (One2many)
        resource_commands = []
        for res_data in data.get('Resources', []):
            res_vals = self.env['mindbody.appointment.resource']._prepare_appointment_resource(res_data)
            if res_vals:
                resource_commands.append((0, 0, res_vals))

        # Prepare add-ons (One2many)
        addon_commands = []
        for addon_data in data.get('AddOns', []):
            addon_vals = self.env['mindbody.appointment.add.on']._prepare_appointment_add_on(addon_data)
            if addon_vals:
                addon_commands.append((0, 0, addon_vals))

        appointment_vals = {
            'gender_preference': data.get('GenderPreference', 'None'),
            'duration': data.get('Duration', 0),
            'provider_id': data.get('ProviderId'),
            'appointment_id': data.get('Id'),
            'status': data.get('Status', 'None'),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'notes': data.get('Notes'),
            'partner_external_id': data.get('PartnerExternalId'),
            'staff_requested': data.get('StaffRequested', False),
            'program_id': data.get('ProgramId'),
            'session_type_id': data.get('SessionTypeId'),
            'location_id': data.get('LocationId'),
            'staff_id_int': data.get('StaffId'),
            'client_id': data.get('ClientId'),
            'first_appointment': data.get('FirstAppointment', False),
            'is_waitlist': data.get('IsWaitlist', False),
            'waitlist_entry_id': data.get('WaitlistEntryId', 0),
            'client_service_id': data.get('ClientServiceId', 0),
            'online_description': data.get('OnlineDescription'),

            # One2many fields
            'resource_ids': resource_commands if resource_commands else None,
            'add_on_ids': addon_commands if addon_commands else None,
        }

        # Add Many2one fields with create commands
        if staff_name_vals:
            appointment_vals['staff_name_id'] = (0, 0, staff_name_vals)

        # Remove None values
        appointment_vals = {k: v for k, v in appointment_vals.items() if v is not None and v is not False}

        return appointment_vals

    # mindbody_staff_appointment.py

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_appointment_ids=None):
        """
        Synchronize staff appointments from Mindbody to Odoo.
        Note: Staff appointments are typically synced as part of staff sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            staff_appointment_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Staff appointments are synced automatically during staff sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
