import logging
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyAppointmentAddOn(models.Model):
    _name = 'mindbody.appointment.add.on'
    _description = 'Mindbody Appointment Add On'

    appointment_id = fields.Many2one('mindbody.appointment', string='Appointment')
    appointment_cart_id = fields.Many2one('mindbody.appointment.cart', string='Appointment Cart')
    staff_appointment_id = fields.Many2one('mindbody.staff.appointment', string='Staff Appointment')
    add_on_id = fields.Integer(string='Add On ID')
    name = fields.Char(string='Name')
    staff_id = fields.Integer(string='Staff ID')
    type_id = fields.Integer(string='Type ID')
    num_deducted = fields.Integer(string='Num Deducted')
    category_id = fields.Integer(string='Category ID')
    category = fields.Char(string='Category')
    session_type_id = fields.Integer(string='Session Type ID')
    start_time = fields.Datetime(string='Start Time')
    duration_override_in_minutes = fields.Integer(string='Duration Override In Minutes')
    resource_ids = fields.One2many('mindbody.appointment.resource', 'add_on_id', string='Resources')
    notes = fields.Text(string='Notes')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

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

    def _prepare_appointment_add_on(self, data):
        """Prepare appointment add-on values from API response"""
        resource_commands = []
        for res_data in data.get('Resources', []):
            res_vals = self.env['mindbody.appointment.resource']._prepare_appointment_resource(res_data)
            if res_vals:
                resource_commands.append((0, 0, res_vals))

        add_on_vals = {
            'add_on_id': data.get('Id'),
            'name': data.get('Name'),
            'staff_id': data.get('StaffId'),
            'type_id': data.get('TypeId'),
            'num_deducted': data.get('NumDeducted', 0),
            'category_id': data.get('CategoryId'),
            'category': data.get('Category'),
            'session_type_id': data.get('SessionTypeId'),
            'start_time': self._parse_datetime(data.get('StartTime')),
            'duration_override_in_minutes': data.get('DurationOverrideInMinutes', 0),
            'notes': data.get('Notes'),
        }

        if resource_commands:
            add_on_vals['resource_ids'] = resource_commands

        return {k: v for k, v in add_on_vals.items() if v is not None and v is not False}

    def synchronize(self, from_date=None, to_date=None, limit=None, add_on_ids=None):
        """Synchronize appointment add-ons from Mindbody to Odoo"""
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if add_on_ids:
                params['AddOnIDs'] = ','.join(map(str, add_on_ids)) if isinstance(add_on_ids, list) else add_on_ids

            response = api.get_appointment_addons(params=params)
            add_ons_data = response.get('AddOns', []) if isinstance(response, dict) else []

            if not add_ons_data:
                return stats

            for add_on_data in add_ons_data:
                try:
                    add_on_id = add_on_data.get('Id')
                    if not add_on_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.search([('add_on_id', '=', add_on_id)], limit=1)
                    add_on_vals = self._prepare_appointment_add_on(add_on_data)

                    if existing:
                        if 'resource_ids' in add_on_vals:
                            existing.resource_ids.unlink()
                        existing.write(add_on_vals)
                        stats['updated'] += 1
                    else:
                        self.create(add_on_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error: {str(e)}", exc_info=True)

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Add-ons sync failed: {str(e)}")

        return stats
