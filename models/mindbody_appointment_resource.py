import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyAppointmentResource(models.Model):
    _name = 'mindbody.appointment.resource'
    _description = 'Mindbody Appointment Resource'

    resource_id = fields.Integer(string='Resource ID')
    name = fields.Char(string='Name')
    resource_type = fields.Selection([('Staff', 'Staff')], default='Staff', string='Resource Type')
    appointment_id = fields.Many2one('mindbody.appointment', string='Appointment')
    appointment_cart_id = fields.Many2one('mindbody.appointment.cart', string='Appointment Cart')
    staff_appointment_id = fields.Many2one('mindbody.staff.appointment', string='Staff Appointment')
    add_on_id = fields.Many2one('mindbody.appointment.add.on', string='Add On')

    def _prepare_appointment_resource(self, data):
        """Prepare appointment resource values from API response"""
        resource_vals = {
            'resource_id': data.get('Id'),
            'name': data.get('Name'),
            'resource_type': data.get('Type') or data.get('ResourceType'),
        }
        return {k: v for k, v in resource_vals.items() if v is not None and v is not False}

    def synchronize(self):
        """Delegate to parent Appointment sync"""
        _logger.info("Appointment Resource sync triggered — delegating to Appointment sync...")
        return self.env['mindbody.appointment'].synchronize()

# import logging
#
# _logger = logging.getLogger(__name__)
# from odoo import models, fields
#
#
# class MindbodyAppointmentResource(models.Model):
#     _name = 'mindbody.appointment.resource'
#     _description = 'Mindbody Appointment Resource'
#
#     resource_id = fields.Integer(string='Resource ID')
#     name = fields.Char(string='Name')
#     resource_type = fields.Selection([('Staff', 'Staff')], default='Staff', string='Resource Type')
#     appointment_id = fields.Many2one('mindbody.appointment', string='Appointment')
#     appointment_cart_id = fields.Many2one('mindbody.appointment.cart', string='Appointment Cart')
#     staff_appointment_id = fields.Many2one('mindbody.staff.appointment', string='Staff Appointment')
#     add_on_id = fields.Many2one('mindbody.appointment.add.on', string='Add On')
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_appointment_resource(self, data):
#         """
#         Prepare appointment resource values from API response.
#
#         Args:
#             data (dict): Appointment resource data from Mindbody API
#
#         Returns:
#             dict: Values ready for mindbody.appointment.resource create/write
#         """
#         resource_vals = {
#             'resource_id': data.get('Id'),
#             'name': data.get('Name'),
#             'resource_type': data.get('Type') or data.get('ResourceType'),
#         }
#         return {k: v for k, v in resource_vals.items() if v is not None and v is not False}
#
#     def synchronize(self):
#         """
#         Synchronize appointment resources from Mindbody to Odoo.
#         Note: Appointment resources are typically synced as part of appointment sync.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Not used for this endpoint
#             resource_ids (list, optional): Not used for this endpoint
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         _logger.info("Appointment resources are synced automatically during appointment sync")
#         return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
