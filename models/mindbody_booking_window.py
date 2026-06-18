# mindbody_booking_window.py
from odoo import models, fields


class MindbodyBookingWindow(models.Model):
    _name = 'mindbody.booking.window'
    _description = 'Mindbody Booking Window'

    start_date_time = fields.Datetime(string='Start Date Time')
    end_date_time = fields.Datetime(string='End Date Time')
    daily_start_time = fields.Datetime(string='Daily Start Time')
    daily_end_time = fields.Datetime(string='Daily End Time')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_booking_window(self, data):
        """
        Prepare booking window values from API response.
        
        Args:
            data (dict): Booking window data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.booking.window create/write
        """
        self.ensure_one()

        booking_window_vals = {
            'start_date_time': data.get('StartDateTime'),
            'end_date_time': data.get('EndDateTime'),
            'daily_start_time': data.get('DailyStartTime'),
            'daily_end_time': data.get('DailyEndTime'),
        }

        # Remove None values
        booking_window_vals = {k: v for k, v in booking_window_vals.items() if v is not None and v is not False}

        return booking_window_vals
