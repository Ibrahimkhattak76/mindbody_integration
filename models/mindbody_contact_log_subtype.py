import logging

_logger = logging.getLogger(__name__)
# mindbody_contact_log_subtype.py
from odoo import models, fields


class MindbodyContactLogSubtype(models.Model):
    _name = 'mindbody.contact.log.subtype'
    _description = 'Mindbody Contact Log Subtype'

    contact_log_type_id = fields.Many2one('mindbody.contact.log.type', string='Contact Log Type')

    sub_type_id = fields.Integer(string='Sub Type ID')
    name = fields.Char(string='Name')

    # mindbody_contact_log_subtype.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contact_log_subtype(self, data):
        """
        Prepare contact log subtype values from API response.
        
        Args:
            data (dict): Contact log subtype data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.contact.log.subtype create/write
        """
        self.ensure_one()

        subtype_vals = {
            'sub_type_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        subtype_vals = {k: v for k, v in subtype_vals.items() if v is not None and v is not False}

        return subtype_vals

    # mindbody_contact_log_subtype.py

    def synchronize(self, from_date=None, to_date=None, limit=None, subtype_ids=None):
        """
        Synchronize contact log subtypes from Mindbody to Odoo.
        Note: Contact log subtypes are typically synced as part of contact log sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            subtype_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Contact log subtypes are synced automatically during contact log sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
