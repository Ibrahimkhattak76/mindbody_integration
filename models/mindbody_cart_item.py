import logging

_logger = logging.getLogger(__name__)
# mindbody_cart_item.py
from odoo import models, fields


class MindbodyCartItem(models.Model):
    _name = 'mindbody.cart.item'
    _description = 'Mindbody Cart Item'

    cart_id = fields.Many2one('mindbody.shopping.cart', string='Cart')

    item = fields.Text(string='Item')  # JSON field or generic
    sales_notes = fields.Text(string='Sales Notes')
    discount_amount = fields.Float(string='Discount Amount')
    visit_ids = fields.Char(string='Visit IDs')  # JSON list
    appointment_ids = fields.Char(string='Appointment IDs')  # JSON list
    appointment_cart_ids = fields.One2many('mindbody.appointment.cart', 'cart_item_id', string='Appointments')
    item_id = fields.Integer(string='Item ID')
    quantity = fields.Float(string='Quantity')

    # mindbody_cart_item.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_cart_item(self, data):
        """
        Prepare cart item values from API response.
        
        Args:
            data (dict): Cart item data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.cart.item create/write
        """
        self.ensure_one()

        # Prepare appointments (One2many)
        appointment_commands = []
        for appt_data in data.get('Appointments', []):
            appt_vals = self.env['mindbody.appointment.cart']._prepare_appointment_cart(appt_data)
            if appt_vals:
                appointment_commands.append((0, 0, appt_vals))

        cart_item_vals = {
            'item': str(data.get('Item', {})),
            'sales_notes': data.get('SalesNotes'),
            'discount_amount': data.get('DiscountAmount', 0.0),
            'visit_ids': str(data.get('VisitIds', [])),
            'appointment_ids': str(data.get('AppointmentIds', [])),
            'item_id': data.get('Id', 0),
            'quantity': data.get('Quantity', 0.0),

            # One2many fields
            'appointment_cart_ids': appointment_commands if appointment_commands else None,
        }

        # Remove None values
        cart_item_vals = {k: v for k, v in cart_item_vals.items() if v is not None and v is not False}

        return cart_item_vals

    # mindbody_cart_item.py

    def synchronize(self, from_date=None, to_date=None, limit=None, cart_item_ids=None):
        """
        Synchronize cart items from Mindbody to Odoo.
        Note: Cart items are typically synced as part of shopping cart sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            cart_item_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Cart items are synced automatically during shopping cart sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
