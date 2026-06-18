import logging

_logger = logging.getLogger(__name__)
# mindbody_user_group.py
from odoo import models, fields


class MindbodyUserGroup(models.Model):
    _name = 'mindbody.user.group'
    _description = 'Mindbody User Group'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    permission_group_name = fields.Char(string='Permission Group Name')
    ip_restricted = fields.Boolean(string='IP Restricted')
    allowed_permission_ids = fields.One2many('mindbody.permission', 'user_group_allowed_id',
                                             string='Allowed Permissions')
    denied_permission_ids = fields.One2many('mindbody.permission', 'user_group_denied_id', string='Denied Permissions')

    # mindbody_user_group.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_user_group(self, data):
        """
        Prepare user group values from API response.
        
        Args:
            data (dict): User group data from Mindbody API (from /staff/staffpermissions endpoint)
            
        Returns:
            dict: Values ready for mindbody.user.group create/write
        """
        self.ensure_one()

        # Prepare allowed permissions (One2many)
        allowed_commands = []
        for perm_name in data.get('AllowedPermissions', []):
            perm_vals = self.env['mindbody.permission']._prepare_permission({
                'name': perm_name,
                'type': 'allowed'
            })
            if perm_vals:
                allowed_commands.append((0, 0, perm_vals))

        # Prepare denied permissions (One2many)
        denied_commands = []
        for perm_name in data.get('DeniedPermissions', []):
            perm_vals = self.env['mindbody.permission']._prepare_permission({
                'name': perm_name,
                'type': 'denied'
            })
            if perm_vals:
                denied_commands.append((0, 0, perm_vals))

        user_group_vals = {
            'permission_group_name': data.get('PermissionGroupName'),
            'ip_restricted': data.get('IpRestricted', False),

            # One2many fields
            'allowed_permission_ids': allowed_commands if allowed_commands else None,
            'denied_permission_ids': denied_commands if denied_commands else None,
        }

        # Remove None values
        user_group_vals = {k: v for k, v in user_group_vals.items() if v is not None and v is not False}

        return user_group_vals

    # mindbody_user_group.py

    def synchronize(self, from_date=None, to_date=None, limit=None, user_group_ids=None):
        """
        Synchronize user groups from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            user_group_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting user group sync")

            # Fetch user groups from Mindbody API
            response = api.get_staff_staffpermissions()
            user_group_data = response.get('UserGroup', {}) if isinstance(response, dict) else {}

            if not user_group_data:
                _logger.info("No user group found to sync")
                return stats

            # Check if user group already exists (there should only be one per staff)
            # Note: This endpoint might require staff ID as parameter

            # Prepare user group values
            user_group_vals = self._prepare_user_group(user_group_data)

            existing = self.search([], limit=1)
            if existing:
                existing.write(user_group_vals)
                stats['updated'] += 1
                _logger.info("Updated user group")
            else:
                self.create(user_group_vals)
                stats['created'] += 1
                _logger.info("Created user group")

            _logger.info(f"User group sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync user groups")
            stats['errors'] += 1
            raise UserError(f"User group sync failed: {str(e)}")

        return stats
