import logging

_logger = logging.getLogger(__name__)
# mindbody_permission.py
from odoo import models, fields


class MindbodyPermission(models.Model):
    _name = 'mindbody.permission'
    _description = 'Mindbody Permission'

    user_group_allowed_id = fields.Many2one('mindbody.user.group', string='User Group (Allowed)')
    user_group_denied_id = fields.Many2one('mindbody.user.group', string='User Group (Denied)')

    name = fields.Selection([
        ('ManageClassAndEventDescriptions', 'Manage Class And Event Descriptions')
    ], string='Permission Name')

    # mindbody_permission.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_permission(self, data):
        """
        Prepare permission values from API response.
        
        Args:
            data (dict): Permission data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.permission create/write
        """
        self.ensure_one()

        permission_vals = {
            'name': data.get('name') or data.get('Name') or data.get('permission_name'),
        }

        # Remove None values
        permission_vals = {k: v for k, v in permission_vals.items() if v is not None and v is not False}

        return permission_vals

    # mindbody_permission.py

    def synchronize(self, from_date=None, to_date=None, limit=None, permission_ids=None):
        """
        Synchronize permissions from Mindbody to Odoo.
        Note: Permissions are typically synced as part of user group sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            permission_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Permissions are synced automatically during user group sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
