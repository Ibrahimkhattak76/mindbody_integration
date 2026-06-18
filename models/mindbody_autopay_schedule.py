import logging

_logger = logging.getLogger(__name__)
# mindbody_autopay_schedule.py
from odoo import models, fields


class MindbodyAutopaySchedule(models.Model):
    _name = 'mindbody.autopay.schedule'
    _description = 'Mindbody Autopay Schedule'

    frequency_type = fields.Char(string='Frequency Type')
    frequency_value = fields.Integer(string='Frequency Value')
    frequency_time_unit = fields.Char(string='Frequency Time Unit')

    # mindbody_autopay_schedule.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_autopay_schedule(self, data):
        """
        Prepare autopay schedule values from API response.
        
        Args:
            data (dict): Autopay schedule data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.autopay.schedule create/write
        """
        self.ensure_one()

        autopay_schedule_vals = {
            'frequency_type': data.get('FrequencyType'),
            'frequency_value': data.get('FrequencyValue', 0),
            'frequency_time_unit': data.get('FrequencyTimeUnit'),
        }

        # Remove None values
        autopay_schedule_vals = {k: v for k, v in autopay_schedule_vals.items() if v is not None and v is not False}

        return autopay_schedule_vals

    # mindbody_autopay_schedule.py

    def synchronize(self, from_date=None, to_date=None, limit=None, autopay_schedule_ids=None):
        """
        Synchronize autopay schedules from Mindbody to Odoo.
        Note: Autopay schedules are typically synced as part of contract sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            autopay_schedule_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Autopay schedules are synced automatically during contract sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
