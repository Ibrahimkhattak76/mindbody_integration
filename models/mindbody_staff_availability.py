import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_availability.py
from odoo import models, fields


class MindbodyStaffAvailability(models.Model):
    _name = 'mindbody.staff.availability'
    _description = 'Mindbody Staff Availability'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    availability_id = fields.Integer(string='Availability ID')
    staff_obj = fields.Text(string='Staff Object')  # JSON field or relation
    session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')
    program_ids = fields.One2many('mindbody.program', 'staff_availability_id', string='Programs')
    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    bookable_end_date_time = fields.Datetime(string='Bookable End Date Time')
    location_id = fields.Many2one('mindbody.location', string='Location')
    prep_time = fields.Integer(string='Prep Time')
    finish_time = fields.Integer(string='Finish Time')
    is_masked = fields.Boolean(string='Is Masked')
    show_public = fields.Boolean(string='Show Public')
    resource_availability_ids = fields.One2many('mindbody.resource.availability', 'staff_availability_id',
                                                string='Resource Availabilities')

    # mindbody_staff_availability.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_availability(self, data):
        """
        Prepare staff availability values from API response.

        Args:
            data (dict): Staff availability data from Mindbody API

        Returns:
            dict: Values ready for mindbody.staff.availability create/write
        """
        self.ensure_one()

        # Prepare session type (Many2one)
        session_type_vals = None
        if data.get('SessionType'):
            session_type_vals = self.env['mindbody.session.type']._prepare_session_type(data['SessionType'])

        # Prepare programs (One2many)
        program_commands = []
        for prog_data in data.get('Programs', []):
            prog_vals = self.env['mindbody.program']._prepare_program(prog_data)
            if prog_vals:
                program_commands.append((0, 0, prog_vals))

        # Prepare location (Many2one)
        location_vals = None
        if data.get('Location'):
            location_vals = self.env['mindbody.location']._prepare_location(data['Location'])

        # Prepare resource availabilities (One2many)
        resource_avail_commands = []
        for res_avail_data in data.get('ResourceAvailabilities', []):
            res_avail_vals = self.env['mindbody.resource.availability']._prepare_resource_availability(res_avail_data)
            if res_avail_vals:
                resource_avail_commands.append((0, 0, res_avail_vals))

        availability_vals = {
            'availability_id': data.get('Id'),
            'staff_obj': str(data.get('Staff', {})),
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'bookable_end_date_time': data.get('BookableEndDateTime'),
            'prep_time': data.get('PrepTime', 0),
            'finish_time': data.get('FinishTime', 0),
            'is_masked': data.get('IsMasked', False),
            'show_public': data.get('ShowPublic', False),

            # One2many fields
            'program_ids': program_commands if program_commands else None,
            'resource_availability_ids': resource_avail_commands if resource_avail_commands else None,
        }

        # Add Many2one fields with create commands
        if session_type_vals:
            availability_vals['session_type_id'] = (0, 0, session_type_vals)
        if location_vals:
            availability_vals['location_id'] = (0, 0, location_vals)

        # Remove None values
        availability_vals = {k: v for k, v in availability_vals.items() if v is not None and v is not False}

        return availability_vals

    # mindbody_staff_availability.py

    def synchronize(self, from_date=None, to_date=None, limit=None, availability_ids=None):
        """
        Synchronize staff availabilities from Mindbody to Odoo.
        Note: Staff availabilities are typically synced as part of staff sync.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            availability_ids (list, optional): Not used for this endpoint

        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Staff availabilities are synced automatically during staff sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
