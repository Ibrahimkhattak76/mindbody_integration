import logging
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyShoppingCart(models.Model):
    _name = 'mindbody.shopping.cart'
    _description = 'Mindbody Shopping Cart'

    cart_id = fields.Char(string='Cart ID')
    cart_item_ids = fields.One2many('mindbody.cart.item', 'cart_id', string='Cart Items')
    sub_total = fields.Float(string='Sub Total')
    discount_total = fields.Float(string='Discount Total')
    tax_total = fields.Float(string='Tax Total')
    grand_total = fields.Float(string='Grand Total')
    transaction_ids = fields.One2many('mindbody.transaction', 'cart_id', string='Transactions')
    sale_id = fields.Integer(string='Sale ID')
    class_ids = fields.One2many('mindbody.class.cart', 'cart_id', string='Classes')
    appointment_ids = fields.One2many('mindbody.appointment.cart', 'cart_id', string='Appointments')
    enrollment_ids = fields.One2many('mindbody.enrollment', 'cart_id', string='Enrollments')

    # ============================================
    # Helper Methods
    # ============================================

    def _parse_datetime(self, value):
        """Convert ISO 8601 datetime to Odoo format"""
        if not value:
            return False
        try:
            if 'Z' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            elif 'T' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            else:
                return value
            return fields.Datetime.to_string(dt)
        except Exception as e:
            _logger.warning(f"Failed to parse datetime '{value}': {str(e)}")
            return False

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_shopping_cart(self, data):
        """
        Prepare shopping cart values from API response.

        This is typically called after checkout, not from a list endpoint.
        """
        # ✅ Removed self.ensure_one() - this is a helper method

        cart_data = data.get('ShoppingCart', {})

        # Prepare cart items
        item_commands = []
        for item_data in cart_data.get('CartItems', []):
            item_vals = self.env['mindbody.cart.item']._prepare_cart_item(item_data)
            if item_vals:
                item_commands.append((0, 0, item_vals))

        # Prepare transactions
        transaction_commands = []
        for trans_data in cart_data.get('Transactions', []):
            trans_vals = self.env['mindbody.transaction']._prepare_transaction(trans_data)
            if trans_vals:
                transaction_commands.append((0, 0, trans_vals))

        # Prepare classes
        class_commands = []
        for class_data in data.get('Classes', []):
            class_vals = self.env['mindbody.class.cart']._prepare_class_cart(class_data)
            if class_vals:
                class_commands.append((0, 0, class_vals))

        # Prepare appointments
        appointment_commands = []
        for appt_data in data.get('Appointments', []):
            appt_vals = self.env['mindbody.appointment.cart']._prepare_appointment_cart(appt_data)
            if appt_vals:
                appointment_commands.append((0, 0, appt_vals))

        # Prepare enrollments
        enrollment_commands = []
        for enroll_data in data.get('Enrollments', []):
            enroll_vals = self.env['mindbody.enrollment']._prepare_enrollment(enroll_data)
            if enroll_vals:
                enrollment_commands.append((0, 0, enroll_vals))

        cart_vals = {
            'cart_id': cart_data.get('Id'),
            'sub_total': cart_data.get('SubTotal', 0.0),
            'discount_total': cart_data.get('DiscountTotal', 0.0),
            'tax_total': cart_data.get('TaxTotal', 0.0),
            'grand_total': cart_data.get('GrandTotal', 0.0),
            'sale_id': cart_data.get('SaleId'),
        }

        if item_commands:
            cart_vals['cart_item_ids'] = item_commands
        if transaction_commands:
            cart_vals['transaction_ids'] = transaction_commands
        if class_commands:
            cart_vals['class_ids'] = class_commands
        if appointment_commands:
            cart_vals['appointment_ids'] = appointment_commands
        if enrollment_commands:
            cart_vals['enrollment_ids'] = enrollment_commands

        # Remove None values
        return {k: v for k, v in cart_vals.items() if v is not None and v is not False}

    # ============================================
    # Synchronize Method
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, cart_ids=None):
        """
        Shopping carts are created during checkout, not synced from a list endpoint.

        This button is informational only - carts are created via checkout API.
        """
        _logger.info("Shopping Cart sync triggered")
        _logger.info("Note: Shopping carts are created during checkout process, not synced from API")
        _logger.info("Use the Checkout API to create shopping carts")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Shopping Cart Info',
                'message': 'Shopping carts are created during checkout process, not synced from API. Use the Checkout API to create carts.',
                'type': 'info',
                'sticky': False,
            }
        }
