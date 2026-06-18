import logging

_logger = logging.getLogger(__name__)
# mindbody_class_visit.py
from odoo import models, fields


class MindbodyClassVisit(models.Model):
    _name = 'mindbody.class.visit'
    _description = 'Mindbody Class Visit'

    class_instance_id = fields.Many2one('mindbody.class.instance', string='Class Instance')

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

    # mindbody_class_visit.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_visit(self, data):
        """
        Prepare class visit values from API response.
        
        Args:
            data (dict): Class visit data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.class.visit create/write
        """
        self.ensure_one()

        # Prepare service (Many2one)
        service_vals = None
        if data.get('Service'):
            service_vals = self.env['mindbody.service']._prepare_service(data['Service'])

        visit_vals = {
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
        }

        # Add Many2one fields with create commands
        if service_vals:
            visit_vals['service_id_ref'] = (0, 0, service_vals)

        # Remove None values
        visit_vals = {k: v for k, v in visit_vals.items() if v is not None and v is not False}

        return visit_vals

    # mindbody_class_visit.py

    def synchronize(self, from_date=None, to_date=None, limit=None, class_visit_ids=None):
        """
        Synchronize class visits from Mindbody to Odoo.
        Note: Class visits are typically synced as part of class instance sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            class_visit_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Class visits are synced automatically during class instance sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    def synchronize_class_visits(self, class_id=None):
        """
        Synchronize class visits detail from Mindbody to Odoo.
        
        Args:
            class_id (int, required): Specific class ID to sync visits for
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            if not class_id:
                stats['errors'] += 1
                return stats

            # Prepare parameters
            params = {'classId': class_id}

            # Fetch class visits detail from Mindbody API
            response = api.get_class_classvisits(params=params)
            class_data = response.get('Class', {}) if isinstance(response, dict) else {}

            if not class_data:
                return stats

            # Update or create class instance
            class_vals = self.env['mindbody.class.instance']._prepare_class_instance(class_data)
            existing_class = self.env['mindbody.class.instance'].search([('class_id', '=', class_id)], limit=1)

            if existing_class:
                existing_class.write(class_vals)
                stats['updated'] += 1
            else:
                self.env['mindbody.class.instance'].create(class_vals)
                stats['created'] += 1

            # Process visits
            visits_data = class_data.get('Visits', [])
            for visit_data in visits_data:
                visit_vals = self._prepare_class_visit(visit_data)
                visit_id = visit_data.get('Id')
                if visit_id:
                    existing = self.search([('visit_id', '=', visit_id)], limit=1)
                    if existing:
                        existing.write(visit_vals)
                        stats['updated'] += 1
                    else:
                        self.create(visit_vals)
                        stats['created'] += 1

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Class visits sync failed: {str(e)}")

        return stats
