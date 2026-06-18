import logging
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyAppointment(models.Model):
    _name = 'mindbody.appointment'
    _description = 'Mindbody Appointment'

    appointment_id = fields.Integer(string='Appointment ID')
    gender_preference = fields.Selection([
        ('None', 'None'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ], string='Gender Preference', default='None')
    duration = fields.Integer(string='Duration')
    provider_id = fields.Char(string='Provider ID')
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
    resource_ids = fields.One2many('mindbody.appointment.resource', 'appointment_id', string='Resources')
    add_on_ids = fields.One2many('mindbody.appointment.add.on', 'appointment_id', string='Add Ons')
    online_description = fields.Text(string='Online Description')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    itinerary_ids = fields.One2many('mindbody.appointment', 'parent_appointment_id', string='Itinerary')
    parent_appointment_id = fields.Many2one('mindbody.appointment', string='Parent Appointment')
    preparation_time = fields.Integer(string='Preparation Time')
    finish_time = fields.Integer(string='Finish Time')
    error_id = fields.Many2one('mindbody.error.info', string='Error')
    request_id = fields.Integer(string='Request ID')
    add_on_appointment_id = fields.Integer(string='Add On Appointment ID')

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

    def _prepare_appointment(self, data):
        """Prepare appointment values from API response"""

        staff = self._get_or_sync_staff(data.get('StaffId'))

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

        appointment_vals = {
            'appointment_id': data.get('Id'),
            'gender_preference': data.get('GenderPreference', 'None'),
            'duration': data.get('Duration', 0),
            'provider_id': data.get('ProviderId'),
            'status': data.get('Status', 'None'),
            'start_date_time': self._parse_datetime(data.get('StartDateTime')),
            'end_date_time': self._parse_datetime(data.get('EndDateTime')),
            'notes': data.get('Notes'),
            'partner_external_id': data.get('PartnerExternalId'),
            'staff_requested': data.get('StaffRequested', False),
            'program_id': data.get('ProgramId'),
            'session_type_id': data.get('SessionTypeId'),
            'location_id': data.get('LocationId'),
            'staff_id': staff.id if staff else False,
            'staff_external_id': data.get('StaffId'),
            'client_id': data.get('ClientId'),
            'first_appointment': data.get('FirstAppointment', False),
            'is_waitlist': data.get('IsWaitlist', False),
            'waitlist_entry_id': data.get('WaitlistEntryId', 0),
            'client_service_id': data.get('ClientServiceId', 0),
            'online_description': data.get('OnlineDescription'),
            'preparation_time': data.get('PreparationTime', 0),
            'finish_time': data.get('FinishTime', 0),
            'add_on_appointment_id': data.get('AddOnAppointmentId'),
            'request_id': data.get('RequestId'),
        }

        if resource_commands:
            appointment_vals['resource_ids'] = resource_commands
        if addon_commands:
            appointment_vals['add_on_ids'] = addon_commands

        return {k: v for k, v in appointment_vals.items() if v is not None}

    def synchronize(self, from_date=None, to_date=None, limit=None, appointment_ids=None):
        """
        Synchronize appointments from Mindbody to Odoo.

        Args:
            from_date (str, optional): Start date for appointments
            to_date (str, optional): End date for appointments
            limit (int, optional): Maximum number of records to fetch
            appointment_ids (list, optional): Specific appointment IDs to sync

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if appointment_ids:
                params['AppointmentIDs'] = ','.join(map(str, appointment_ids)) if isinstance(appointment_ids,
                                                                                             list) else appointment_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            _logger.info(f"Starting appointment sync with params: {params}")
            response = api.get_appointment_staffappointments(params=params)
            dummy_data = [
                {
                    "GenderPreference": "Female",
                    "Duration": 60,
                    "ProviderId": "PROV-101",
                    "Id": 2001,
                    "Status": "Confirmed",
                    "StartDateTime": "2026-04-05T08:00:00Z",
                    "EndDateTime": "2026-04-05T09:00:00Z",
                    "Notes": "Initial physiotherapy session",
                    "PartnerExternalId": "EXT-2001",
                    "StaffRequested": True,
                    "ProgramId": 10,
                    "SessionTypeId": 5,
                    "LocationId": 1,
                    "StaffId": 501,
                    "Staff": {
                        "Id": 501,
                        "FirstName": "Ayesha",
                        "LastName": "Khan",
                        "DisplayName": "Ayesha Khan"
                    },
                    "ClientId": "CL-1001",
                    "FirstAppointment": True,
                    "IsWaitlist": False,
                    "WaitlistEntryId": 0,
                    "ClientServiceId": 3001,
                    "Resources": [
                        {"Id": 11, "Name": "Therapy Room 1"}
                    ],
                    "AddOns": [
                        {"Id": 101, "Name": "Hot Pack", "StaffId": 501, "TypeId": 5}
                    ],
                    "OnlineDescription": "Physiotherapy consultation"
                },
                {
                    "GenderPreference": "Male",
                    "Duration": 45,
                    "ProviderId": "PROV-102",
                    "Id": 2002,
                    "Status": "Completed",
                    "StartDateTime": "2026-04-05T10:00:00Z",
                    "EndDateTime": "2026-04-05T10:45:00Z",
                    "Notes": "Follow-up check",
                    "PartnerExternalId": "EXT-2002",
                    "StaffRequested": False,
                    "ProgramId": 11,
                    "SessionTypeId": 6,
                    "LocationId": 2,
                    "StaffId": 502,
                    "Staff": {
                        "Id": 502,
                        "FirstName": "Ahmed",
                        "LastName": "Raza",
                        "DisplayName": "Ahmed Raza"
                    },
                    "ClientId": "CL-1002",
                    "FirstAppointment": False,
                    "IsWaitlist": False,
                    "WaitlistEntryId": 0,
                    "ClientServiceId": 3002,
                    "Resources": [
                        {"Id": 12, "Name": "Room B"}
                    ],
                    "AddOns": [],
                    "OnlineDescription": "Routine follow-up"
                },
                {
                    "GenderPreference": "None",
                    "Duration": 30,
                    "ProviderId": "PROV-103",
                    "Id": 2003,
                    "Status": "Booked",
                    "StartDateTime": "2026-04-06T12:30:00Z",
                    "EndDateTime": "2026-04-06T13:00:00Z",
                    "Notes": "Quick consultation",
                    "PartnerExternalId": "EXT-2003",
                    "StaffRequested": True,
                    "ProgramId": 12,
                    "SessionTypeId": 7,
                    "LocationId": 1,
                    "StaffId": 503,
                    "Staff": {
                        "Id": 503,
                        "FirstName": "Usman",
                        "LastName": "Ali",
                        "DisplayName": "Usman Ali"
                    },
                    "ClientId": "CL-1003",
                    "FirstAppointment": False,
                    "IsWaitlist": True,
                    "WaitlistEntryId": 9001,
                    "ClientServiceId": 3003,
                    "Resources": [
                        {"Id": 13, "Name": "Consultation Room"}
                    ],
                    "AddOns": [
                        {"Id": 102, "Name": "Priority Service", "StaffId": 503, "TypeId": 7}
                    ],
                    "OnlineDescription": "Short consult"
                },
                {
                    "GenderPreference": "Female",
                    "Duration": 90,
                    "ProviderId": "PROV-104",
                    "Id": 2004,
                    "Status": "Cancelled",
                    "StartDateTime": "2026-04-07T15:00:00Z",
                    "EndDateTime": "2026-04-07T16:30:00Z",
                    "Notes": "Client cancelled last minute",
                    "PartnerExternalId": "EXT-2004",
                    "StaffRequested": False,
                    "ProgramId": 13,
                    "SessionTypeId": 8,
                    "LocationId": 3,
                    "StaffId": 504,
                    "Staff": {
                        "Id": 504,
                        "FirstName": "Fatima",
                        "LastName": "Noor",
                        "DisplayName": "Fatima Noor"
                    },
                    "ClientId": "CL-1004",
                    "FirstAppointment": False,
                    "IsWaitlist": False,
                    "WaitlistEntryId": 0,
                    "ClientServiceId": 3004,
                    "Resources": [
                        {"Id": 14, "Name": "Deluxe Room"}
                    ],
                    "AddOns": [],
                    "OnlineDescription": "Extended therapy session"
                }
            ]
            appointments_data = dummy_data  # response.get('Appointments', []) if isinstance(response, dict) else []
            print(appointments_data)

            if not appointments_data:
                _logger.info("No appointments found to sync")
                return stats

            _logger.info(f"Fetched {len(appointments_data)} appointments from Mindbody")

            for appointment_data in appointments_data:
                try:
                    appointment_id = appointment_data.get('Id')
                    if not appointment_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.search([('appointment_id', '=', appointment_id)], limit=1)
                    appointment_vals = self._prepare_appointment(appointment_data)

                    if existing:
                        if 'resource_ids' in appointment_vals:
                            existing.resource_ids.unlink()
                        if 'add_on_ids' in appointment_vals:
                            existing.add_on_ids.unlink()
                        existing.write(appointment_vals)
                        stats['updated'] += 1
                    else:
                        self.create(appointment_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing appointment {appointment_data.get('Id')}: {str(e)}", exc_info=True)

            _logger.info(f"Appointment sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync appointments")
            raise UserError(f"Appointment sync failed: {str(e)}")

        return stats
