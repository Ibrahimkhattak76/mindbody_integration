import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_name.py
from odoo import models, fields


class MindbodyStaffName(models.Model):
    _name = 'mindbody.staff.name'
    _description = 'Mindbody Staff Name'

    staff_id = fields.Integer(string='Staff ID')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    display_name = fields.Char(string='Display Name')

    # ============================================
    # Prepare Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_name_ids=None):
        """
        Synchronize staff names from Mindbody to Odoo.
        Note: Staff names are typically synced as part of staff sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            staff_name_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Staff names are synced automatically during staff sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
