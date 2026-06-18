import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_settings.py
from odoo import models, fields


class MindbodyStaffSettings(models.Model):
    _name = 'mindbody.staff.settings'
    _description = 'Mindbody Staff Settings'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    use_staff_nicknames = fields.Boolean(string='Use Staff Nicknames')
    show_staff_last_names_on_schedules = fields.Boolean(string='Show Staff Last Names On Schedules')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_settings(self, data):
        """
        Prepare staff settings values from API response.
        
        Args:
            data (dict): Staff settings data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.staff.settings create/write
        """
        settings_vals = {
            'use_staff_nicknames': data.get('UseStaffNicknames', False),
            'show_staff_last_names_on_schedules': data.get('ShowStaffLastNamesOnSchedules', False),
        }
        return {k: v for k, v in settings_vals.items() if v is not None and v is not False}

    def synchronize(self):
        """
        Synchronize staff settings from Mindbody to Odoo.
        Note: Staff settings are typically synced as part of staff sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            settings_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Staff settings are synced automatically during staff sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
