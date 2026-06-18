import logging

_logger = logging.getLogger(__name__)
# mindbody_upcoming_autopay_event.py
from odoo import models, fields


class MindbodyUpcomingAutopayEvent(models.Model):
    _name = 'mindbody.upcoming.autopay.event'
    _description = 'Mindbody Upcoming Autopay Event'

    client_contract_id = fields.Many2one('mindbody.client.contract', string='Client Contract')

    client_contract_id_int = fields.Integer(string='Client Contract ID')
    charge_amount = fields.Float(string='Charge Amount')
    subtotal = fields.Float(string='Subtotal')
    tax = fields.Float(string='Tax')
    payment_method = fields.Selection([
        ('Other', 'Other'),
        ('CreditCard', 'Credit Card'),
        ('Debit', 'Debit'),
        ('ACH', 'ACH')
    ], string='Payment Method', default='Other')
    schedule_date = fields.Datetime(string='Schedule Date')
    product_id = fields.Integer(string='Product ID')

    # mindbody_upcoming_autopay_event.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_upcoming_autopay_event(self, data):
        """
        Prepare upcoming autopay event values from API response.
        
        Args:
            data (dict): Upcoming autopay event data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.upcoming.autopay.event create/write
        """
        self.ensure_one()

        event_vals = {
            'client_contract_id_int': data.get('ClientContractId'),
            'charge_amount': data.get('ChargeAmount', 0.0),
            'subtotal': data.get('Subtotal', 0.0),
            'tax': data.get('Tax', 0.0),
            'payment_method': data.get('PaymentMethod', 'Other'),
            'schedule_date': data.get('ScheduleDate'),
            'product_id': data.get('ProductId'),
        }

        # Remove None values
        event_vals = {k: v for k, v in event_vals.items() if v is not None and v is not False}

        return event_vals

    # mindbody_upcoming_autopay_event.py

    def synchronize(self, from_date=None, to_date=None, limit=None, event_ids=None):
        """
        Synchronize upcoming autopay events from Mindbody to Odoo.
        Note: Upcoming autopay events are typically synced as part of client contract sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            event_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Upcoming autopay events are synced automatically during client contract sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
