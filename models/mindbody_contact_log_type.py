import logging

_logger = logging.getLogger(__name__)
# mindbody_contact_log_type.py
from odoo import models, fields


class MindbodyContactLogType(models.Model):
    _name = 'mindbody.contact.log.type'
    _description = 'Mindbody Contact Log Type'

    contact_log_id = fields.Many2one('mindbody.contact.log', string='Contact Log')

    type_id = fields.Integer(string='Type ID')
    name = fields.Char(string='Name')
    sub_type_ids = fields.One2many('mindbody.contact.log.subtype', 'contact_log_type_id', string='Sub Types')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_contact_log_type.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contact_log_type(self, data):
        """
        Prepare contact log type values from API response.
        
        Args:
            data (dict): Contact log type data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.contact.log.type create/write
        """
        self.ensure_one()

        # Prepare subtypes (One2many)
        subtype_commands = []
        for sub_data in data.get('SubTypes', []):
            sub_vals = self.env['mindbody.contact.log.subtype']._prepare_contact_log_subtype(sub_data)
            if sub_vals:
                subtype_commands.append((0, 0, sub_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        type_vals = {
            'type_id': data.get('Id'),
            'name': data.get('Name'),

            # One2many fields
            'sub_type_ids': subtype_commands if subtype_commands else None,
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            type_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        type_vals = {k: v for k, v in type_vals.items() if v is not None and v is not False}

        return type_vals

    # mindbody_contact_log_type.py

    def synchronize(self, from_date=None, to_date=None, limit=None, contact_log_type_ids=None):
        """
        Synchronize contact log types from Mindbody to Odoo.
        Note: Contact log types are typically synced as part of contact log sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            contact_log_type_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Contact log types are synced automatically during contact log sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
